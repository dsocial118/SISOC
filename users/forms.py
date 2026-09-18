# pylint: disable=too-many-lines
import json
from datetime import timedelta

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.models import Group, Permission, User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import FileExtensionValidator
from django.db import transaction
from django.utils.crypto import get_random_string
from django.utils import timezone

from core.constants import UserGroups
from core.models import Provincia
from core.validators import solo_digitos, validate_cuit
from users.form_catalogs import obtener_queryset_formulario
from users.models import (
    AccesoComedorPWA,
    CoordinadorEquipoTecnicoPWA,
    Profile,
    RelevadorCalleProvincia,
    TerritorialComedorProvincia,
)
from users.profile_utils import get_profile_or_none
from users.services_datacalle import (
    es_administrador_datacalle,
    es_solo_app,
    validar_alcance_coordinador,
)
from users.services_delegation import effective_delegatable_groups_qs
from users.services_pwa import (
    PWA_ASSIGNABLE_PERMISSION_CODES,
    PWA_USUARIOS_PERMISSION_CODE,
    deactivate_coordinador_equipo_tecnico_pwa_access,
    deactivate_representante_accesses,
    get_organizacion_ids,
    is_pwa_user,
    sync_coordinador_equipo_tecnico_pwa_access,
    sync_representante_accesses,
)
from users.services_bulk_credentials import get_bulk_credentials_send_type_choices
from users.territorial_scope import (
    clean_territorial_scope_payload,
    get_full_province_scope_ids,
    serialize_profile_scopes,
    sync_profile_territorial_scopes,
)


class UsernameEmailPasswordResetForm(PasswordResetForm):
    username = forms.CharField(label="Usuario", max_length=150, required=True)

    def get_users(self, email):
        username = (self.cleaned_data.get("username") or "").strip()
        try:
            user = User.objects.get(username=username, is_active=True)
        except User.DoesNotExist:
            return ()

        email_matches = (user.email or "").casefold() == (email or "").casefold()
        if not email_matches:
            return ()
        return (user,)


MOBILE_RENDICION_PERMISSION_CODE = "rendicioncuentasmensual.manage_mobile_rendicion"
PWA_OPERATION_PERMISSION_CODES = PWA_ASSIGNABLE_PERMISSION_CODES | {
    PWA_USUARIOS_PERMISSION_CODE,
}
PWA_OPERATION_PERMISSION_FIELDS = {
    "puede_gestionar_colaboradores_pwa": (
        "pwa.manage_colaboradores_pwa",
        "Puede gestionar colaboradores mobile",
    ),
    "puede_gestionar_usuarios_pwa": (
        "pwa.manage_usuarios_pwa",
        "Puede crear y gestionar usuarios mobile",
    ),
    "puede_gestionar_nomina_pwa": (
        "pwa.manage_nomina_pwa",
        "Puede gestionar nomina mobile",
    ),
    "puede_gestionar_prestaciones_mensuales_pwa": (
        "pwa.manage_prestaciones_mensuales_pwa",
        "Puede gestionar prestaciones mensuales mobile",
    ),
}


ROLE_PERMISSION_QUERYSET = (
    Permission.objects.select_related("content_type")
    .filter(
        content_type__app_label="auth",
        codename__startswith="role_",
    )
    .order_by("name")
)

PWA_SELECTION_FIELDS = (
    "es_coordinador_equipo_tecnico_pwa",
    "duplas_coordinador_pwa",
    "comedores_adicionales_coordinador_pwa",
    "puede_gestionar_rendiciones_mobile",
    *PWA_OPERATION_PERMISSION_FIELDS,
    "tipo_asociacion_pwa",
    "organizaciones_pwa",
    "comedores_pwa",
)


CDI_ABM_RESTRICTED_GROUPS = (
    UserGroups.SIMEPI_ADMINISTRADOR,
    UserGroups.SIMEPI_EQUIPO_NACIONAL,
    UserGroups.SIMEPI_EGP,
    UserGroups.CDI_REFERENTE_CENTRO,
)

CDI_ABM_RESTRICTED_FIELDS = (
    "es_representante_pwa",
    *PWA_SELECTION_FIELDS,
    "user_permissions",
    "es_coordinador",
    "duplas_asignadas",
    "grupos_asignables",
    "roles_asignables",
)


def _validation_error_messages(error):
    if hasattr(error, "messages"):
        return error.messages
    return [str(error)]


class TerritorialScopeFormMixin:
    def _setup_territorial_scope_fields(self, profile=None):
        initial_scopes = serialize_profile_scopes(profile)
        self.initial_territorial_scopes = initial_scopes
        initial_json = json.dumps(initial_scopes)
        self.fields["territorial_scopes"].initial = initial_json
        if not self.is_bound:
            self.initial["territorial_scopes"] = initial_json

    def _clean_territorial_scope_fields(self, cleaned):
        if not cleaned.get("es_usuario_provincial"):
            cleaned["territorial_scopes_data"] = []
            return cleaned

        raw_scopes = cleaned.get("territorial_scopes") or "[]"
        try:
            payload = json.loads(raw_scopes)
        except json.JSONDecodeError:
            self.add_error(
                "territorial_scopes",
                "El formato de alcances territoriales no es válido.",
            )
            cleaned["territorial_scopes_data"] = []
            return cleaned

        if payload in (None, [], "") and cleaned.get("provincia"):
            payload = [
                {
                    "provincia_id": cleaned["provincia"].pk,
                    "municipio_id": None,
                    "localidad_id": None,
                }
            ]

        try:
            cleaned["territorial_scopes_data"] = clean_territorial_scope_payload(
                payload
            )
        except DjangoValidationError as error:
            for message in _validation_error_messages(error):
                self.add_error("territorial_scopes", message)
            cleaned["territorial_scopes_data"] = []
        return cleaned

    def _validate_simepi_egp_scope(self, cleaned):
        groups = cleaned.get("groups")
        if not groups or not groups.filter(name=UserGroups.SIMEPI_EGP).exists():
            return cleaned

        scopes = cleaned.get("territorial_scopes_data", [])
        has_only_full_provinces = (
            cleaned.get("es_usuario_provincial")
            and bool(scopes)
            and all(
                scope.get("municipio_id") is None and scope.get("localidad_id") is None
                for scope in scopes
            )
        )
        if not has_only_full_provinces:
            self.add_error(
                "territorial_scopes",
                "El grupo SIMEPI - EGP requiere al menos una provincia completa.",
            )
        return cleaned


class BackofficeAuthenticationForm(AuthenticationForm):
    """Bloquea login web para usuarios de uso exclusivo PWA."""

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Usuario o contraseña inválidos.",
    }

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        self.fields[User.USERNAME_FIELD].error_messages[
            "required"
        ] = "Este campo es obligatorio."
        self.fields["password"].error_messages[
            "required"
        ] = "Este campo es obligatorio."

    def clean(self):
        username_field_name = User.USERNAME_FIELD
        username = self.data.get(username_field_name) or ""
        password = self.data.get("password") or ""
        mutable_data = self.data.copy()
        required_message = "Este campo es obligatorio."
        trimmed_username = username.strip()

        mutable_data[username_field_name] = trimmed_username
        self.data = mutable_data

        if not trimmed_username and username_field_name not in self.errors:
            self.add_error(username_field_name, required_message)
        if not password.strip() and "password" not in self.errors:
            self.add_error("password", required_message)
        if self.errors:
            self.data["password"] = ""
            return self.cleaned_data

        try:
            return super().clean()
        except forms.ValidationError:
            self.data["password"] = ""
            raise

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        profile = get_profile_or_none(user)
        saved_mobile = getattr(profile, "configuracion_mobile", {})
        if is_pwa_user(user) or saved_mobile.get("es_coordinador_equipo_tecnico_pwa"):
            raise forms.ValidationError(
                "Este usuario solo puede ingresar desde la PWA.",
                code="pwa_only",
            )
        # RN05: solo el relevador queda afuera. El coordinador y el
        # administrador usan la app y tambien el backoffice.
        if es_solo_app(user):
            raise forms.ValidationError(
                "Este usuario solo puede ingresar desde SISOC - Mobile DataCalle.",
                code="datacalle_only",
            )
        expires_at = getattr(profile, "initial_password_expires_at", None)
        if (
            getattr(profile, "must_change_password", False)
            and expires_at
            and expires_at <= timezone.now()
        ):
            raise forms.ValidationError(
                "La contraseña inicial expiró. Solicite un reinicio a un administrador.",
                code="initial_password_expired",
            )


class UserLoginForm(BackofficeAuthenticationForm):
    """Compatibilidad para configuraciones existentes."""


class ComedorPWASelectMultiple(forms.SelectMultiple):
    """Agrega metadata de organización en las opciones para filtrado dinámico."""

    def create_option(  # pylint: disable=too-many-arguments
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        instance = getattr(value, "instance", None)
        if instance is not None:
            option["attrs"]["data-organizacion-id"] = str(
                instance.organizacion_id or ""
            )
            option["attrs"]["data-organizacion-nombre"] = (
                instance.organizacion.nombre if instance.organizacion_id else ""
            )
        return option


class PWAAccessMixin:
    @staticmethod
    def _get_mobile_rendicion_permission():
        return Permission.objects.get(
            content_type__app_label="rendicioncuentasmensual",
            codename="manage_mobile_rendicion",
        )

    @staticmethod
    def _get_permission_from_code(permission_code):
        app_label, codename = permission_code.split(".", 1)
        return Permission.objects.get(
            content_type__app_label=app_label,
            codename=codename,
        )

    @staticmethod
    def _set_initial_password_flags(
        profile,
        *,
        must_change_password: bool,
        temporary_password_plaintext: str | None = None,
        password_reset_requested_at=None,
    ):
        profile.must_change_password = must_change_password
        profile.password_changed_at = (
            None if must_change_password else profile.password_changed_at
        )
        profile.initial_password_expires_at = (
            timezone.now() + timedelta(hours=settings.INITIAL_PASSWORD_MAX_AGE_HOURS)
            if must_change_password
            else None
        )
        profile.password_reset_requested_at = password_reset_requested_at
        profile.temporary_password_plaintext = temporary_password_plaintext

    def _setup_pwa_fields(self):
        self.fields["es_representante_pwa"] = forms.BooleanField(
            required=False,
            label="Habilitar acceso a SISOC - Mobile",
        )
        self.fields["es_coordinador_equipo_tecnico_pwa"] = forms.BooleanField(
            required=False,
            label="Coordinador de Equipo Técnico",
            help_text="Acceso PWA exclusivo de solo lectura.",
        )
        self.fields["duplas_coordinador_pwa"] = forms.ModelMultipleChoiceField(
            queryset=obtener_queryset_formulario("duplas_asignadas"),
            required=False,
            widget=forms.SelectMultiple(attrs={"class": "select2"}),
            label="Equipos técnicos PWA",
            help_text="El alcance se actualiza automáticamente según sus comedores.",
        )
        self.fields["comedores_adicionales_coordinador_pwa"] = (
            forms.ModelMultipleChoiceField(
                queryset=obtener_queryset_formulario("comedores_pwa"),
                required=False,
                widget=forms.SelectMultiple(attrs={"class": "select2"}),
                label="Comedores adicionales PWA",
            )
        )
        self.fields["puede_gestionar_rendiciones_mobile"] = forms.BooleanField(
            required=False,
            label="Puede gestionar rendiciones mobile",
            help_text="Habilita el módulo Rendición de Cuentas en SISOC - Mobile.",
        )
        for field_name, (_, label) in PWA_OPERATION_PERMISSION_FIELDS.items():
            self.fields[field_name] = forms.BooleanField(
                required=False,
                label=label,
            )
        self.fields["tipo_asociacion_pwa"] = forms.ChoiceField(
            required=False,
            choices=(
                ("", "Seleccione una opción"),
                (
                    AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
                    "Usuario asociado a Organización",
                ),
                (
                    AccesoComedorPWA.TIPO_ASOCIACION_ESPACIO,
                    "Usuario asociado a Espacio",
                ),
            ),
            widget=forms.Select(attrs={"class": "select2"}),
            label="Tipo de asociación mobile",
        )
        self.fields["organizaciones_pwa"] = forms.ModelMultipleChoiceField(
            queryset=obtener_queryset_formulario("organizaciones_pwa"),
            required=False,
            widget=forms.SelectMultiple(attrs={"class": "select2"}),
            label="Organizaciones",
            help_text=(
                "Cada organización habilita automáticamente todos sus comedores "
                "actuales y futuros."
            ),
        )
        self.fields["comedores_pwa"] = forms.ModelMultipleChoiceField(
            queryset=obtener_queryset_formulario("comedores_pwa"),
            required=False,
            widget=ComedorPWASelectMultiple(attrs={"class": "select2"}),
            label="Comedores PWA",
            help_text="Comedores que este usuario representa en la PWA.",
        )

    def _init_pwa_fields(self):
        if not self.instance or not self.instance.pk:
            return
        accesos = AccesoComedorPWA.objects.filter(
            user=self.instance,
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
            activo=True,
        )
        organizacion_ids = get_organizacion_ids(self.instance) or list(
            accesos.exclude(organizacion_id__isnull=True)
            .values_list("organizacion_id", flat=True)
            .distinct()
        )
        tipos_asociacion = sorted(
            {tipo for tipo in accesos.values_list("tipo_asociacion", flat=True) if tipo}
        )
        comedor_ids = list(accesos.values_list("comedor_id", flat=True))
        self.fields["es_representante_pwa"].initial = bool(
            comedor_ids or organizacion_ids
        )
        self.fields["puede_gestionar_rendiciones_mobile"].initial = (
            self.instance.has_perm(MOBILE_RENDICION_PERMISSION_CODE)
        )
        for field_name, (permission_code, _) in PWA_OPERATION_PERMISSION_FIELDS.items():
            self.fields[field_name].initial = self.instance.has_perm(permission_code)
        self.fields["tipo_asociacion_pwa"].initial = (
            tipos_asociacion[0]
            if len(tipos_asociacion) == 1
            else (
                AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION
                if organizacion_ids and not tipos_asociacion
                else ""
            )
        )
        self.fields["organizaciones_pwa"].initial = organizacion_ids
        self.fields["comedores_pwa"].initial = comedor_ids
        coordinator_scope = CoordinadorEquipoTecnicoPWA.objects.filter(
            user=self.instance, activo=True
        ).first()
        if coordinator_scope:
            self.fields["es_representante_pwa"].initial = True
            self.fields["es_coordinador_equipo_tecnico_pwa"].initial = True
            self.fields["duplas_coordinador_pwa"].initial = (
                coordinator_scope.duplas.all()
            )
            self.fields["comedores_adicionales_coordinador_pwa"].initial = (
                coordinator_scope.comedores_adicionales.all()
            )

        profile = get_profile_or_none(self.instance)
        selections = getattr(profile, "configuracion_mobile", {})
        mobile_enabled = self.fields["es_representante_pwa"].initial
        for name in PWA_SELECTION_FIELDS:
            if name in selections and (
                not mobile_enabled
                or (
                    coordinator_scope
                    and name
                    in (
                        "puede_gestionar_rendiciones_mobile",
                        *PWA_OPERATION_PERMISSION_FIELDS,
                    )
                )
            ):
                self.fields[name].initial = selections[name]

    def _is_active_pwa_operator(self) -> bool:
        if not self.instance or not self.instance.pk:
            return False
        return AccesoComedorPWA.objects.filter(
            user=self.instance,
            rol=AccesoComedorPWA.ROL_OPERADOR,
            activo=True,
        ).exists()

    def _sync_mobile_rendicion_permission(self, user):
        permission = self._get_mobile_rendicion_permission()
        if self.cleaned_data.get("puede_gestionar_rendiciones_mobile"):
            user.user_permissions.add(permission)
            return
        user.user_permissions.remove(permission)

    def _sync_pwa_operation_permissions(self, user):
        for field_name, (permission_code, _) in PWA_OPERATION_PERMISSION_FIELDS.items():
            permission = self._get_permission_from_code(permission_code)
            if self.cleaned_data.get(field_name):
                user.user_permissions.add(permission)
            else:
                user.user_permissions.remove(permission)

    @staticmethod
    def _preserve_current_pwa_operation_permission_ids(user):
        permission_ids = []
        effective_codes = (
            set(user.get_all_permissions()) & PWA_OPERATION_PERMISSION_CODES
        )
        for permission_code in effective_codes:
            app_label, codename = permission_code.split(".", 1)
            permission = Permission.objects.filter(
                content_type__app_label=app_label,
                codename=codename,
            ).first()
            if permission:
                permission_ids.append(permission.id)
        return permission_ids

    def _clean_mobile_access_switch(self, cleaned):
        # The legacy field name now acts as the master mobile access switch.
        # Remember selections before normalizing inactive roles and permissions.
        self._mobile_selections = {}
        for name in PWA_SELECTION_FIELDS:
            value = cleaned.get(name)
            if isinstance(self.fields[name], forms.ModelMultipleChoiceField):
                value = (
                    list(value.values_list("pk", flat=True))
                    if value is not None
                    else []
                )
            self._mobile_selections[name] = value
        mobile_enabled = cleaned.get("es_representante_pwa", False)
        if not mobile_enabled:
            cleaned["es_coordinador_equipo_tecnico_pwa"] = False
        if not mobile_enabled or cleaned.get("es_coordinador_equipo_tecnico_pwa"):
            for name in (
                "puede_gestionar_rendiciones_mobile",
                *PWA_OPERATION_PERMISSION_FIELDS,
            ):
                cleaned[name] = False

    def _clean_pwa_fields(self, cleaned):
        self._clean_mobile_access_switch(cleaned)
        es_coordinador_pwa = cleaned.get("es_coordinador_equipo_tecnico_pwa", False)
        es_representante_pwa = (
            cleaned.get("es_representante_pwa", False) and not es_coordinador_pwa
        )
        tipo_asociacion_pwa = cleaned.get("tipo_asociacion_pwa")
        organizaciones_pwa = cleaned.get("organizaciones_pwa")
        comedores_pwa = cleaned.get("comedores_pwa")
        es_coordinador = cleaned.get("es_coordinador", False)

        if es_coordinador_pwa:
            if not cleaned.get("duplas_coordinador_pwa"):
                self.add_error(
                    "duplas_coordinador_pwa",
                    "Seleccione al menos un equipo técnico para el coordinador PWA.",
                )
            if es_coordinador:
                self.add_error(
                    "es_coordinador",
                    "El coordinador PWA es independiente del coordinador SISOC.",
                )
            if cleaned.get("es_territorial_comedor"):
                self.add_error(
                    "es_territorial_comedor",
                    "El coordinador PWA no puede tener acceso territorial.",
                )
            if self.instance and self.instance.pk and self._is_active_pwa_operator():
                self.add_error(
                    "es_coordinador_equipo_tecnico_pwa",
                    "El coordinador PWA no puede tener rol operador activo.",
                )

        if not es_representante_pwa:
            cleaned["tipo_asociacion_pwa"] = ""
            cleaned["organizaciones_pwa"] = self.fields[
                "organizaciones_pwa"
            ].queryset.none()
            cleaned["comedores_pwa"] = self.fields["comedores_pwa"].queryset.none()
            tipo_asociacion_pwa = ""
            organizaciones_pwa = cleaned["organizaciones_pwa"]
            comedores_pwa = cleaned["comedores_pwa"]

        if es_representante_pwa and not (comedores_pwa or organizaciones_pwa):
            self.add_error(
                "comedores_pwa",
                "Debe seleccionar al menos una organización o un comedor para un "
                "representante PWA.",
            )
        if not es_representante_pwa and (
            comedores_pwa or organizaciones_pwa or tipo_asociacion_pwa
        ):
            self.add_error(
                "es_representante_pwa",
                "Marque este campo para asignar comedores PWA.",
            )
        if es_representante_pwa and es_coordinador:
            self.add_error(
                "es_coordinador",
                "Un representante PWA no puede ser coordinador de equipo técnico.",
            )
        if es_representante_pwa and self.instance and self.instance.pk:
            if AccesoComedorPWA.objects.filter(
                user=self.instance,
                rol=AccesoComedorPWA.ROL_OPERADOR,
                activo=True,
            ).exists():
                self.add_error(
                    "es_representante_pwa",
                    "No se puede asignar representante PWA a un usuario operador activo.",
                )

        return cleaned

    def _sync_pwa_access(self, user):
        if not self._is_active_pwa_operator():
            Profile.objects.filter(user=user).update(
                configuracion_mobile=self._mobile_selections
            )
        if self.cleaned_data.get("es_coordinador_equipo_tecnico_pwa"):
            deactivate_representante_accesses(user)
            sync_coordinador_equipo_tecnico_pwa_access(
                user=user,
                duplas=self.cleaned_data["duplas_coordinador_pwa"],
                comedores_adicionales=self.cleaned_data[
                    "comedores_adicionales_coordinador_pwa"
                ],
            )
            return
        deactivate_coordinador_equipo_tecnico_pwa_access(user)
        if not self.cleaned_data.get(
            "es_representante_pwa"
        ) and self._mobile_selections.get("es_coordinador_equipo_tecnico_pwa"):
            scope, _ = CoordinadorEquipoTecnicoPWA.objects.get_or_create(
                user=user, defaults={"activo": False}
            )
            scope.duplas.set(self._mobile_selections["duplas_coordinador_pwa"])
            scope.comedores_adicionales.set(
                self._mobile_selections["comedores_adicionales_coordinador_pwa"]
            )
        if self.cleaned_data.get("es_representante_pwa"):
            organization_ids = set(
                self.cleaned_data["organizaciones_pwa"].values_list("id", flat=True)
            )
            selected_by_id = {
                comedor.id: comedor for comedor in self.cleaned_data["comedores_pwa"]
            }
            for comedor in self.fields["comedores_pwa"].queryset.filter(
                organizacion_id__in=organization_ids
            ):
                selected_by_id[comedor.id] = comedor

            access_specs = []
            for comedor in sorted(selected_by_id.values(), key=lambda item: item.id):
                association_type = (
                    AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION
                    if comedor.organizacion_id in organization_ids
                    else AccesoComedorPWA.TIPO_ASOCIACION_ESPACIO
                )
                access_specs.append(
                    {
                        "comedor_id": comedor.id,
                        "tipo_asociacion": association_type,
                        "organizacion_id": (
                            comedor.organizacion_id
                            if association_type
                            == AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION
                            else None
                        ),
                    }
                )
            sync_representante_accesses(
                user=user,
                access_specs=access_specs,
                organizacion_ids=organization_ids,
                actor=None,
            )
            return
        deactivate_representante_accesses(user)

    def _clean_optional_email(self, cleaned):
        # El email es opcional y puede repetirse entre usuarios; la unicidad
        # vive en username. Solo normalizamos espacios para evitar registros
        # inconsistentes.
        cleaned["email"] = (cleaned.get("email") or "").strip()
        return cleaned


class DelegationScopeMixin:
    actor = None

    def _setup_delegation_fields(self):
        self.fields["grupos_asignables"] = forms.ModelMultipleChoiceField(
            queryset=Group.objects.all().order_by("name"),
            required=False,
            widget=forms.SelectMultiple(attrs={"class": "select2"}),
            label="Grupos que puede asignar",
            help_text=(
                "Define qué grupos podrá asignar este usuario al crear/editar "
                "otros usuarios."
            ),
        )
        self.fields["roles_asignables"] = forms.ModelMultipleChoiceField(
            queryset=ROLE_PERMISSION_QUERYSET,
            required=False,
            widget=forms.SelectMultiple(attrs={"class": "select2"}),
            label="Roles que puede asignar",
            help_text="Permisos auth.role_* delegables a terceros.",
        )

    def _apply_cdi_abm_restrictions(self):
        """Restringe capacidades administrativas para los gestores CDI.

        Los campos quedan deshabilitados, además de ocultos en el template, para
        que un POST construido manualmente no pueda modificar configuraciones
        ajenas al circuito CDI. En edición Django conserva sus valores iniciales.
        """
        actor_groups = (
            set(
                self.actor.groups.filter(
                    name__in=CDI_ABM_RESTRICTED_GROUPS
                ).values_list("name", flat=True)
            )
            if self.actor and not self.actor.is_superuser
            else set()
        )
        self.is_cdi_abm_restricted = bool(actor_groups)
        self.can_manage_mobile_access = not self.is_cdi_abm_restricted
        self.can_manage_direct_permissions = not self.is_cdi_abm_restricted
        self.can_manage_technical_teams = not self.is_cdi_abm_restricted
        self.can_manage_delegation = not self.is_cdi_abm_restricted

        if not self.is_cdi_abm_restricted:
            return

        for field_name in CDI_ABM_RESTRICTED_FIELDS:
            self.fields[field_name].disabled = True

    def _is_unrestricted_actor(self):
        return not self.actor or self.actor.is_superuser

    def _allowed_groups_for_actor(self):
        if self._is_unrestricted_actor():
            return Group.objects.all().order_by("name")

        return effective_delegatable_groups_qs(self.actor).order_by("name")

    def _allowed_roles_for_actor(self):
        if self._is_unrestricted_actor():
            return ROLE_PERMISSION_QUERYSET

        profile = getattr(self.actor, "profile", None)
        if not profile:
            return Permission.objects.none()
        return profile.roles_asignables.filter(
            content_type__app_label="auth",
            codename__startswith="role_",
        ).order_by("name")

    def _scope_assignable_fields_for_actor(self):
        allowed_groups = self._allowed_groups_for_actor()
        allowed_roles = self._allowed_roles_for_actor()
        all_permissions = Permission.objects.select_related("content_type").order_by(
            "content_type__app_label",
            "name",
        )

        # El campo de grupos debe MOSTRAR los grupos actuales del usuario aunque
        # estén fuera del alcance del actor; el alcance real de edición se valida
        # y se preserva por separado (un actor con alcance no puede quitar grupos
        # que no administra). user_permissions ya muestra el catálogo completo.
        if self.instance and self.instance.pk:
            groups_field_qs = (allowed_groups | self.instance.groups.all()).distinct()
        else:
            groups_field_qs = allowed_groups

        self.fields["groups"].queryset = groups_field_qs
        self.fields["user_permissions"].queryset = all_permissions
        self.fields["grupos_asignables"].queryset = allowed_groups
        self.fields["roles_asignables"].queryset = allowed_roles

    def _init_delegation_fields(self, profile):
        if not profile:
            return
        self.fields["grupos_asignables"].initial = profile.grupos_asignables.all()
        self.fields["roles_asignables"].initial = profile.roles_asignables.filter(
            content_type__app_label="auth",
            codename__startswith="role_",
        )

    def _validate_selected_within_allowed(self, cleaned):
        if self._is_unrestricted_actor():
            return

        # Valores actuales del usuario: se permiten conservar aunque estén fuera
        # del alcance del actor (no se pueden AGREGAR nuevos fuera de alcance).
        original_group_ids = (
            set(self.instance.groups.values_list("id", flat=True))
            if self.instance and self.instance.pk
            else set()
        )
        original_perm_ids = (
            set(self.instance.user_permissions.values_list("id", flat=True))
            if self.instance and self.instance.pk
            else set()
        )

        allowed_group_ids = set(
            self._allowed_groups_for_actor().values_list("id", flat=True)
        )
        selected_group_ids = set(
            cleaned.get("groups", Group.objects.none()).values_list("id", flat=True)
        )
        selected_assignable_group_ids = set(
            cleaned.get("grupos_asignables", Group.objects.none()).values_list(
                "id", flat=True
            )
        )

        if not selected_group_ids.issubset(allowed_group_ids | original_group_ids):
            self.add_error(
                "groups",
                "Solo puede asignar grupos habilitados para su usuario.",
            )
        if not selected_assignable_group_ids.issubset(allowed_group_ids):
            self.add_error(
                "grupos_asignables",
                "Solo puede delegar grupos que usted mismo puede asignar.",
            )

        allowed_role_ids = set(
            self._allowed_roles_for_actor().values_list("id", flat=True)
        )
        selected_role_ids = set(
            cleaned.get("user_permissions", Permission.objects.none()).values_list(
                "id", flat=True
            )
        )
        selected_assignable_role_ids = set(
            cleaned.get("roles_asignables", Permission.objects.none()).values_list(
                "id", flat=True
            )
        )

        if not selected_role_ids.issubset(allowed_role_ids | original_perm_ids):
            self.add_error(
                "user_permissions",
                "Solo puede asignar roles habilitados para su usuario.",
            )
        if not selected_assignable_role_ids.issubset(allowed_role_ids):
            self.add_error(
                "roles_asignables",
                "Solo puede delegar roles que usted mismo puede asignar.",
            )

    def _aplicar_grupos_y_permisos(self, user):
        """Asigna grupos y permisos directos preservando los que están fuera del
        alcance del actor: un actor con alcance administra solo lo habilitado y
        no puede quitar grupos/roles que no le corresponden. Un actor sin
        restricción (superusuario) asigna exactamente lo seleccionado."""
        selected_groups = self.cleaned_data.get("groups", [])
        selected_permissions = self.cleaned_data.get("user_permissions", [])

        if self._is_unrestricted_actor():
            user.groups.set(selected_groups)
            user.user_permissions.set(selected_permissions)
            return

        allowed_group_ids = set(
            self._allowed_groups_for_actor().values_list("id", flat=True)
        )
        allowed_role_ids = set(
            self._allowed_roles_for_actor().values_list("id", flat=True)
        )
        original_group_ids = set(user.groups.values_list("id", flat=True))
        original_permission_ids = set(
            user.user_permissions.values_list("id", flat=True)
        )
        selected_group_ids = {group.pk for group in selected_groups}
        selected_permission_ids = {perm.pk for perm in selected_permissions}

        final_group_ids = (selected_group_ids & allowed_group_ids) | (
            original_group_ids - allowed_group_ids
        )
        final_permission_ids = (selected_permission_ids & allowed_role_ids) | (
            original_permission_ids - allowed_role_ids
        )

        user.groups.set(list(final_group_ids))
        user.user_permissions.set(list(final_permission_ids))


class TerritorialComedorFormMixin:
    """Campos del rol "Territorial comedor" (SISOC - Mobile).

    Flag simple sobre ``Profile.es_territorial_comedor`` + alcance por provincia
    en ``TerritorialComedorProvincia``. Es mutuamente excluyente con el
    representante PWA (``es_representante_pwa``): un mismo usuario no puede ser
    ambos. No arrastra la maquinaria del representante (auto-password, limpieza
    de grupos, ocultamiento del backoffice): el territorial es un usuario normal
    con una marca de rol y su alcance provincial.
    """

    def _setup_territorial_comedor_fields(self):
        self.fields["es_territorial_comedor"] = forms.BooleanField(
            required=False,
            label="Habilitar acceso a SISOC - Mobile",
        )
        self.fields["provincias_territorial"] = forms.ModelMultipleChoiceField(
            queryset=Provincia.objects.all().order_by("nombre"),
            required=False,
            widget=forms.SelectMultiple(attrs={"class": "select2"}),
            label="Provincias",
            help_text="Provincias que cubre este territorial en SISOC - Mobile.",
        )

    def _init_territorial_comedor_fields(self, profile):
        if not profile:
            return
        self.fields["es_territorial_comedor"].initial = profile.es_territorial_comedor
        self.fields["provincias_territorial"].initial = list(
            profile.territorial_comedor_provincias.values_list(
                "provincia_id", flat=True
            )
        )

    def _clean_territorial_comedor_fields(self, cleaned):
        es_territorial = cleaned.get("es_territorial_comedor", False)
        es_representante_pwa = cleaned.get("es_representante_pwa", False)
        es_coordinador_pwa = cleaned.get("es_coordinador_equipo_tecnico_pwa", False)
        provincias = cleaned.get("provincias_territorial")

        if es_territorial and (es_representante_pwa or es_coordinador_pwa):
            self.add_error(
                "es_territorial_comedor",
                "Un usuario territorial no puede tener acceso PWA de coordinador "
                "ni representante a la vez.",
            )

        if not es_territorial:
            cleaned["provincias_territorial"] = Provincia.objects.none()
            return cleaned

        if not provincias:
            self.add_error(
                "provincias_territorial",
                "Seleccione al menos una provincia para el territorial.",
            )
        return cleaned

    def _sync_territorial_comedor_provincias(self, profile):
        if not profile.es_territorial_comedor:
            profile.territorial_comedor_provincias.all().delete()
            return
        selected_ids = {
            provincia.id
            for provincia in self.cleaned_data.get("provincias_territorial") or []
        }
        existing_ids = set(
            profile.territorial_comedor_provincias.values_list(
                "provincia_id", flat=True
            )
        )
        to_delete = existing_ids - selected_ids
        if to_delete:
            profile.territorial_comedor_provincias.filter(
                provincia_id__in=to_delete
            ).delete()
        for provincia_id in selected_ids - existing_ids:
            TerritorialComedorProvincia.objects.create(
                profile=profile, provincia_id=provincia_id
            )


class RelevadorCalleFormMixin:
    """Campos del rol "Relevador DataCalle" (SISOC - Mobile).

    Flag ``Profile.es_relevador_calle`` + rol en ``Profile.datacalle_rol`` +
    alcance por provincia en ``RelevadorCalleProvincia``.

    A diferencia del territorial de comedores, el relevador de DataCalle es un
    usuario *solo de la app*: no entra al backoffice (ver
    ``BackofficeAuthenticationForm.confirm_login_allowed``) y por eso es
    excluyente con los otros roles de SISOC - Mobile.
    """

    def _setup_relevador_calle_fields(self):
        # QA-0015: los tres roles de DataCalle no se eligen en el mismo lugar, y
        # eso es lo que confundía. El entrevistador se marca acá porque es un
        # usuario *sólo de la app*; el coordinador y el administrador son
        # usuarios del backoffice y salen del grupo, no de este campo.
        self.fields["es_relevador_calle"] = forms.BooleanField(
            required=False,
            label="Habilitar acceso a SISOC - Mobile DataCalle",
            help_text=(
                "Habilita el acceso a DataCalle para los tres roles. Elegí el "
                "rol acá abajo y el sistema arma el resto: le asigna el grupo "
                "('Coordinador DataCalle' o 'Administrador DataCalle') y el "
                "alcance territorial. Sólo el relevador queda fuera del "
                "backoffice."
            ),
        )
        self.fields["datacalle_rol"] = forms.ChoiceField(
            choices=[("", "---------")] + self._roles_datacalle_para_el_actor(),
            required=False,
            widget=forms.Select(attrs={"class": "select2"}),
            label="Rol en DataCalle",
            help_text=(
                "Administrador Nacional (todo el país), Coordinador Provincial "
                "(su provincia, entra al backoffice y a la app) o Relevador "
                "(sólo la app). Crear coordinadores y elegir provincia es "
                "exclusivo del Administrador Nacional."
            ),
        )
        self.fields["provincias_datacalle"] = forms.ModelMultipleChoiceField(
            queryset=Provincia.objects.all().order_by("nombre"),
            required=False,
            widget=forms.SelectMultiple(attrs={"class": "select2"}),
            label="Provincias",
            help_text="Provincias que releva este usuario en DataCalle.",
        )
        self._acotar_provincias_datacalle_al_actor()

    def _rol_datacalle_actual(self) -> str:
        """Rol que el perfil editado ya tiene (``""`` en un alta)."""
        instance = getattr(self, "instance", None)
        if instance is None or not getattr(instance, "pk", None):
            return ""
        profile = get_profile_or_none(instance)
        return getattr(profile, "datacalle_rol", "") or ""

    def _roles_datacalle_para_el_actor(self):
        """RN02: solo el Administrador Nacional crea roles superiores.

        Un coordinador da de alta relevadores de su provincia y nada mas.

        Dos matices que costaron caro:

        - El rol que el perfil **ya tiene** siempre viaja en las choices. Si no,
          el ``<select>`` no contiene el valor actual, el browser postea ``""``
          y el formulario se rechaza con "Seleccione una opción válida": un
          coordinador no podía ni corregirse el mail, y la única opción que la
          pantalla le ofrecía ("Relevador") lo degradaba a no-staff y lo dejaba
          fuera de SISOC sin vuelta atrás.
        - Sin actor es **fail-closed**. Antes devolvía los tres roles, de modo
          que cualquier camino que instanciara el formulario sin actor podía
          asignar el rol más alto. El superusuario y el administrador siguen
          viendo los tres.
        """
        actor = getattr(self, "actor", None)
        todos = list(Profile.DataCalleRol.choices)
        if getattr(actor, "is_superuser", False) or es_administrador_datacalle(actor):
            return todos
        permitidos = {Profile.DataCalleRol.ENTREVISTADOR, self._rol_datacalle_actual()}
        return [
            (codigo, etiqueta) for codigo, etiqueta in todos if codigo in permitidos
        ]

    def _acotar_provincias_datacalle_al_actor(self):
        """QA-0016: la provincia del entrevistador sale del coordinador.

        Un coordinador provincial no elige en qué provincia da de alta: se
        deriva de su alcance. Con una sola provincia el campo queda fijo y
        deshabilitado, así Django ignora lo que llegue por POST.
        """
        actor = getattr(self, "actor", None)
        if actor is None or getattr(actor, "is_superuser", False):
            return
        provincia_ids = get_full_province_scope_ids(actor)
        if not provincia_ids:
            return
        propias = Provincia.objects.filter(id__in=provincia_ids).order_by("nombre")
        self.fields["provincias_datacalle"].queryset = propias
        if len(provincia_ids) == 1:
            self._provincias_datacalle_fijas = list(provincia_ids)
            self.fields["provincias_datacalle"].initial = list(propias)
            self.fields["provincias_datacalle"].disabled = True
            self.fields["provincias_datacalle"].help_text = (
                "Se deriva de tu alcance territorial."
            )

    @staticmethod
    def _provincias_datacalle_del_perfil(profile):
        """Provincia que el perfil ya tiene, leída de donde vive según el rol.

        El entrevistador la tiene en ``RelevadorCalleProvincia`` y el
        coordinador en ``ProfileTerritorialScope``; el administrador es
        nacional y no tiene ninguna. Leer siempre la primera tabla dejaba el
        campo vacío al editar a un coordinador y el ``clean`` lo rechazaba por
        "Seleccione la provincia".
        """
        if profile.datacalle_rol == Profile.DataCalleRol.COORDINADOR:
            return get_full_province_scope_ids(profile)
        if profile.datacalle_rol == Profile.DataCalleRol.ADMINISTRADOR:
            return []
        return list(
            profile.relevador_calle_provincias.values_list("provincia_id", flat=True)
        )

    def _init_relevador_calle_fields(self, profile):
        if not profile:
            return
        self.fields["es_relevador_calle"].initial = profile.es_relevador_calle
        self.fields["datacalle_rol"].initial = profile.datacalle_rol
        actuales = self._provincias_datacalle_del_perfil(profile)
        fijas = getattr(self, "_provincias_datacalle_fijas", None)
        if not fijas:
            self.fields["provincias_datacalle"].initial = actuales
            return

        # El campo quedó fijo al alcance del actor, así que el initial es esa
        # provincia y nada más. Antes se unía con las que el perfil ya tuviera,
        # para no borrarle a un relevador una provincia que el actor no
        # administra; con RN01 —una sola provincia por usuario— esa unión daría
        # dos y bloquearía la edición. El caso que protegía tampoco deberia
        # existir: la RN03 limita al coordinador a su provincia y
        # `get_relevadores_administrables` ya se lo impone.
        self.fields["provincias_datacalle"].initial = fijas
        self.fields["provincias_datacalle"].queryset = Provincia.objects.filter(
            id__in=fijas
        ).order_by("nombre")

    def _clean_relevador_calle_fields(self, cleaned):
        es_relevador = cleaned.get("es_relevador_calle", False)
        provincias = cleaned.get("provincias_datacalle")

        if not es_relevador:
            cleaned["datacalle_rol"] = ""
            cleaned["provincias_datacalle"] = Provincia.objects.none()
            return cleaned

        # Solo-app: no puede sumar los roles mobile de comedores.
        if cleaned.get("es_representante_pwa", False):
            self.add_error(
                "es_relevador_calle",
                "Un relevador de DataCalle no puede tener acceso como "
                "representante de SISOC - Mobile a la vez.",
            )
        if cleaned.get("es_territorial_comedor", False):
            self.add_error(
                "es_relevador_calle",
                "Un relevador de DataCalle no puede ser territorial de comedores "
                "a la vez.",
            )

        rol = cleaned.get("datacalle_rol")
        if not rol:
            self.add_error(
                "datacalle_rol",
                "Seleccione el rol del relevador de DataCalle.",
            )

        if rol == Profile.DataCalleRol.ADMINISTRADOR:
            # El Administrador Nacional no tiene provincia: pedirle una y
            # después ignorarla sólo confunde al operador.
            cleaned["provincias_datacalle"] = Provincia.objects.none()
            provincias = cleaned["provincias_datacalle"]
        # RN01: exactamente una. El mensaje dice el porque, no solo el limite.
        elif not provincias:
            self.add_error(
                "provincias_datacalle",
                "Seleccione la provincia del usuario de DataCalle.",
            )
        elif len(provincias) > 1:
            self.add_error(
                "provincias_datacalle",
                "Un usuario de DataCalle pertenece a una sola provincia.",
            )

        # RN08: no alcanza con no ofrecer la opcion en el selector. Se rechaza
        # sólo cuando el rol *cambia* a uno que el actor no puede asignar:
        # reenviar el rol que el perfil ya tenía no es una escalada, y tratarlo
        # como tal dejaba a los coordinadores sin poder guardar su propio
        # registro.
        rol_actual = self._rol_datacalle_actual()
        permitidos = {codigo for codigo, _ in self._roles_datacalle_para_el_actor()}
        if rol and rol != rol_actual and rol not in permitidos:
            self.add_error(
                "datacalle_rol",
                "No tenes permiso para asignar ese rol de DataCalle.",
            )
        return self._derivar_alcance_datacalle(cleaned)

    def _derivar_alcance_datacalle(self, cleaned):
        """D1: el operador elige un rol y el sistema arma el alcance.

        Esto nunca se había implementado, y el agujero era grave: la provincia
        elegida se escribía en ``RelevadorCalleProvincia``, que sólo lee el
        entrevistador. Un coordinador creado por el formulario quedaba con
        ``es_usuario_provincial=False`` y sin ``ProfileTerritorialScope``, o
        sea **sin restricción** en el backoffice (veía, editaba, borraba y
        cerraba operativos de todo el país, con el equipo y sus DNI) y con
        alcance vacío en la app.

        Se corre después de las validaciones de rol y provincia, y pisa lo que
        haya dejado ``_clean_territorial_scope_fields``: el alcance de un
        usuario de DataCalle lo decide el rol, no el panel territorial.
        """
        rol = cleaned.get("datacalle_rol")
        if rol == Profile.DataCalleRol.COORDINADOR:
            provincias = list(cleaned.get("provincias_datacalle") or [])
            if len(provincias) != 1:
                return cleaned
            cleaned["es_usuario_provincial"] = True
            cleaned["territorial_scopes_data"] = [
                {
                    "provincia_id": provincias[0].pk,
                    "municipio_id": None,
                    "localidad_id": None,
                }
            ]
        elif rol == Profile.DataCalleRol.ADMINISTRADOR:
            # El alcance nacional es, literalmente, no tener alcance: así lo
            # leen `get_datacalle_provincia_ids` y `_provincia_ids_del_usuario`.
            cleaned["es_usuario_provincial"] = False
            cleaned["territorial_scopes_data"] = []
        return cleaned

    def _validar_provincia_unica_coordinador(self, cleaned):
        """RN01/D3 en el formulario: el coordinador tiene una provincia completa.

        El servicio la vuelve a validar al guardar (``validar_alcance_coordinador``);
        acá el error se muestra en el campo en vez de reventar la transacción.
        """
        if cleaned.get("datacalle_rol") != Profile.DataCalleRol.COORDINADOR:
            return cleaned
        scopes = cleaned.get("territorial_scopes_data") or []
        completos = [
            scope
            for scope in scopes
            if not scope.get("municipio_id") and not scope.get("localidad_id")
        ]
        if len(completos) != 1 or not cleaned.get("es_usuario_provincial"):
            self.add_error(
                "provincias_datacalle",
                "Un Coordinador Provincial de DataCalle debe tener exactamente "
                "una provincia completa como alcance territorial.",
            )
        return cleaned

    def _sync_grupo_datacalle(self, user):
        """D1: el grupo del backoffice sale del rol, no de una carga manual.

        La ayuda del formulario promete que el sistema lo asigna solo; antes
        había que acordarse de tildar el grupo a mano y, si el operador no lo
        hacía, el coordinador entraba a SISOC sin permisos de DataCalle.
        """
        grupos_por_rol = {
            Profile.DataCalleRol.COORDINADOR: "Coordinador DataCalle",
            Profile.DataCalleRol.ADMINISTRADOR: "Administrador DataCalle",
        }
        nombre = grupos_por_rol.get(self.cleaned_data.get("datacalle_rol"))
        if not nombre:
            return
        grupo = Group.objects.filter(name=nombre).first()
        if grupo is not None:
            user.groups.add(grupo)

    def _sync_relevador_calle_provincias(self, profile):
        # ``RelevadorCalleProvincia`` es la tabla del entrevistador y de nadie
        # más: el coordinador tiene su provincia en ``ProfileTerritorialScope``
        # y el administrador no tiene ninguna. Escribir filas acá para los tres
        # roles era la mitad del bug de alcance, así que además se limpian las
        # que hubiera dejado un guardado anterior.
        rol = self.cleaned_data.get("datacalle_rol", "")
        if not profile.es_relevador_calle or rol != Profile.DataCalleRol.ENTREVISTADOR:
            profile.relevador_calle_provincias.all().delete()
            return
        selected_ids = {
            provincia.id
            for provincia in self.cleaned_data.get("provincias_datacalle") or []
        }
        existing_ids = set(
            profile.relevador_calle_provincias.values_list("provincia_id", flat=True)
        )
        to_delete = existing_ids - selected_ids
        if to_delete:
            profile.relevador_calle_provincias.filter(
                provincia_id__in=to_delete
            ).delete()
        for provincia_id in selected_ids - existing_ids:
            RelevadorCalleProvincia.objects.create(
                profile=profile, provincia_id=provincia_id
            )


class UserCreationForm(
    TerritorialScopeFormMixin,
    PWAAccessMixin,
    TerritorialComedorFormMixin,
    RelevadorCalleFormMixin,
    DelegationScopeMixin,
    forms.ModelForm,
):
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")
    dni = forms.CharField(max_length=16, required=False, label="DNI")
    cuil = forms.CharField(max_length=16, required=False, label="CUIL")
    tipo_usuario = forms.ChoiceField(
        choices=Profile.TipoUsuario.choices,
        widget=forms.RadioSelect,
        label="Tipo de usuario",
        help_text=(
            "De dónde viene la persona: interno del organismo, provincial o "
            "externo. Es informativo y no otorga permisos."
        ),
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        label="Grupos",
    )
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.select_related("content_type").order_by(
            "content_type__app_label", "name"
        ),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        label="Permisos directos",
        help_text=(
            "Permisos adicionales específicos para este usuario, "
            "independientes de sus grupos."
        ),
    )
    es_usuario_provincial = forms.BooleanField(
        required=False,
        label="Es usuario provincial",
    )
    provincia = forms.ModelChoiceField(
        queryset=Provincia.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "select2"}),
        label="Provincia",
    )
    territorial_scopes = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
        label="Alcances territoriales",
    )
    es_coordinador = forms.BooleanField(
        required=False,
        label="Es Coordinador de Equipo Técnico",
    )
    duplas_asignadas = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        label="Equipos técnicos (Duplas) asignadas",
        help_text="Duplas activas disponibles (con o sin comedores asignados)",
    )
    rol = forms.CharField(
        max_length=100,
        required=False,
        label="Rol (descriptivo)",
        help_text=(
            "Texto libre para describir el puesto. No define permisos: los "
            "permisos salen de los grupos."
        ),
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "dni",
            "cuil",
            "tipo_usuario",
            "groups",
            "user_permissions",
            "es_usuario_provincial",
            "provincia",
            "territorial_scopes",
            "es_coordinador",
            "duplas_asignadas",
            "last_name",
            "first_name",
            "rol",
        ]

    def __init__(self, *args, **kwargs):
        self.actor = kwargs.pop("actor", None)
        super().__init__(*args, **kwargs)
        self.fields["duplas_asignadas"].queryset = obtener_queryset_formulario(
            "duplas_asignadas"
        )
        self._setup_pwa_fields()
        self._setup_territorial_comedor_fields()
        self._setup_relevador_calle_fields()
        self._setup_delegation_fields()
        self._scope_assignable_fields_for_actor()
        self.fields["email"].required = False
        self.fields["password"].required = False
        self.generated_password = None
        self.password_was_auto_generated = False
        self._setup_territorial_scope_fields()
        self._apply_cdi_abm_restrictions()

    def clean(self):
        cleaned = super().clean()
        cleaned = self._clean_optional_email(cleaned)
        if (
            not cleaned.get("es_representante_pwa")
            and not (cleaned.get("password") or "").strip()
        ):
            self.add_error("password", "Este campo es obligatorio.")
        cleaned = self._clean_territorial_scope_fields(cleaned)
        cleaned = self._validate_simepi_egp_scope(cleaned)
        if cleaned.get("es_coordinador") and not cleaned.get("duplas_asignadas"):
            self.add_error("duplas_asignadas", "Seleccione al menos una dupla.")
        self._validate_selected_within_allowed(cleaned)
        cleaned = self._clean_pwa_fields(cleaned)
        cleaned = self._clean_territorial_comedor_fields(cleaned)
        cleaned = self._clean_relevador_calle_fields(cleaned)
        return self._validar_provincia_unica_coordinador(cleaned)

    def save(self, commit=True):
        with transaction.atomic():
            return self._save_atomic(commit=commit)

    def _configure_created_user(self, user):
        if self.cleaned_data.get(
            "es_representante_pwa", False
        ) or self.cleaned_data.get("es_coordinador_equipo_tecnico_pwa", False):
            self.generated_password = get_random_string(12)
            user.set_password(self.generated_password)
            user.is_staff = False
            self.password_was_auto_generated = True
            return
        user.set_password(self.cleaned_data["password"])
        self.generated_password = None
        self.password_was_auto_generated = False
        # Solo el relevador es usuario sin backoffice (RN05). El coordinador y
        # el administrador tambien llevan `es_relevador_calle` —les habilita la
        # app— pero entran a SISOC.
        if self.cleaned_data.get("datacalle_rol") == "entrevistador":
            user.is_staff = False
            return
        if self.cleaned_data.get("es_coordinador", False):
            user.is_staff = True

    def _save_user_security_and_permissions(self, user):
        if self.cleaned_data.get("es_coordinador_equipo_tecnico_pwa", False):
            user.groups.clear()
            user.user_permissions.clear()
            return
        elif self.cleaned_data.get("es_representante_pwa", False):
            user.groups.clear()
            pwa_permission_ids = self._preserve_current_pwa_operation_permission_ids(
                user
            )
            user.user_permissions.clear()
            if pwa_permission_ids:
                user.user_permissions.add(*pwa_permission_ids)
        else:
            self._aplicar_grupos_y_permisos(user)
            self._sync_grupo_datacalle(user)
        self._sync_mobile_rendicion_permission(user)
        if self.cleaned_data.get("es_representante_pwa", False):
            self._sync_pwa_operation_permissions(user)

    def _save_user_profile(self, user):
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.es_usuario_provincial = self.cleaned_data.get(
            "es_usuario_provincial", False
        )
        profile.dni = self.cleaned_data.get("dni", "")
        profile.cuil = self.cleaned_data.get("cuil", "")
        profile.tipo_usuario = self.cleaned_data["tipo_usuario"]
        profile.provincia = None
        profile.es_coordinador = self.cleaned_data.get("es_coordinador", False)
        profile.es_territorial_comedor = self.cleaned_data.get(
            "es_territorial_comedor", False
        )
        profile.es_relevador_calle = self.cleaned_data.get("es_relevador_calle", False)
        profile.datacalle_rol = self.cleaned_data.get("datacalle_rol", "")
        profile.rol = self.cleaned_data.get("rol")
        profile.must_change_password = True
        profile.password_changed_at = None
        profile.initial_password_expires_at = timezone.now() + timedelta(
            hours=settings.INITIAL_PASSWORD_MAX_AGE_HOURS
        )
        profile.temporary_password_plaintext = self.generated_password
        profile.save()
        self._sync_territorial_comedor_provincias(profile)
        self._sync_relevador_calle_provincias(profile)
        sync_profile_territorial_scopes(
            profile,
            self.cleaned_data.get("territorial_scopes_data", []),
        )
        validar_alcance_coordinador(profile)
        # Evita devolver un profile cacheado con valores viejos tras el signal de User.
        user.refresh_from_db()
        profile.grupos_asignables.set(self.cleaned_data.get("grupos_asignables", []))
        profile.roles_asignables.set(self.cleaned_data.get("roles_asignables", []))
        return profile

    @staticmethod
    def _sync_coordinator_duplas(profile, duplas):
        if profile.es_coordinador and duplas:
            profile.duplas_asignadas.set(duplas)
            return
        profile.duplas_asignadas.clear()

    @staticmethod
    def _clear_permission_caches(user):
        for attr in ("_perm_cache", "_user_perm_cache"):
            if hasattr(user, attr):
                delattr(user, attr)

    def _save_atomic(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "")
        self._configure_created_user(user)

        if commit:
            user.save()
            self._save_user_security_and_permissions(user)
            profile = self._save_user_profile(user)
            duplas = self.cleaned_data.get("duplas_asignadas", [])
            self._sync_coordinator_duplas(profile, duplas)
            self._sync_pwa_access(user)

        self._clear_permission_caches(user)
        return user


class CustomUserChangeForm(
    TerritorialScopeFormMixin,
    PWAAccessMixin,
    TerritorialComedorFormMixin,
    RelevadorCalleFormMixin,
    DelegationScopeMixin,
    forms.ModelForm,
):
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Contraseña (dejar en blanco para no cambiarla)",
        required=False,
    )
    dni = forms.CharField(max_length=16, required=False, label="DNI")
    cuil = forms.CharField(max_length=16, required=False, label="CUIL")
    tipo_usuario = forms.ChoiceField(
        choices=Profile.TipoUsuario.choices,
        widget=forms.RadioSelect,
        label="Tipo de usuario",
        help_text=(
            "De dónde viene la persona: interno del organismo, provincial o "
            "externo. Es informativo y no otorga permisos."
        ),
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        label="Grupos",
    )
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.select_related("content_type").order_by(
            "content_type__app_label", "name"
        ),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        label="Permisos directos",
        help_text=(
            "Permisos adicionales específicos para este usuario, "
            "independientes de sus grupos."
        ),
    )
    es_usuario_provincial = forms.BooleanField(
        required=False,
        label="Es usuario provincial",
    )
    provincia = forms.ModelChoiceField(
        queryset=Provincia.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "select2"}),
        label="Provincia",
    )
    territorial_scopes = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
        label="Alcances territoriales",
    )
    es_coordinador = forms.BooleanField(
        required=False,
        label="Es Coordinador de Equipo Técnico",
    )
    duplas_asignadas = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        label="Equipos técnicos (Duplas) asignadas",
        help_text="Duplas activas disponibles (con o sin comedores asignados)",
    )
    rol = forms.CharField(
        max_length=100,
        required=False,
        label="Rol (descriptivo)",
        help_text=(
            "Texto libre para describir el puesto. No define permisos: los "
            "permisos salen de los grupos."
        ),
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "dni",
            "cuil",
            "tipo_usuario",
            "groups",
            "user_permissions",
            "es_usuario_provincial",
            "provincia",
            "territorial_scopes",
            "es_coordinador",
            "duplas_asignadas",
            "last_name",
            "first_name",
            "rol",
        ]

    def __init__(self, *args, **kwargs):
        self.actor = kwargs.pop("actor", None)
        super().__init__(*args, **kwargs)
        self.fields["duplas_asignadas"].queryset = obtener_queryset_formulario(
            "duplas_asignadas"
        )
        self._setup_pwa_fields()
        self._setup_territorial_comedor_fields()
        self._setup_relevador_calle_fields()
        self._setup_delegation_fields()
        self._scope_assignable_fields_for_actor()
        self.fields["email"].required = False
        self._original_password_hash = self.instance.password
        self.fields["password"].initial = ""
        self._init_pwa_fields()

        try:
            prof = self.instance.profile
        except Profile.DoesNotExist:
            prof = None

        self._setup_territorial_scope_fields(prof)
        self._init_territorial_comedor_fields(prof)
        self._init_relevador_calle_fields(prof)
        if prof:
            self.fields["dni"].initial = prof.dni
            self.fields["cuil"].initial = prof.cuil
            self.fields["tipo_usuario"].initial = prof.tipo_usuario
            self.fields["es_usuario_provincial"].initial = prof.es_usuario_provincial
            self.fields["provincia"].initial = prof.provincia
            self.fields["es_coordinador"].initial = prof.es_coordinador
            self.fields["duplas_asignadas"].initial = prof.duplas_asignadas.all()
            self.fields["rol"].initial = prof.rol
            self._init_delegation_fields(prof)
        self._apply_cdi_abm_restrictions()

    def clean(self):
        cleaned = super().clean()
        cleaned = self._clean_optional_email(cleaned)
        cleaned = self._clean_territorial_scope_fields(cleaned)
        cleaned = self._validate_simepi_egp_scope(cleaned)
        if cleaned.get("es_coordinador") and not cleaned.get("duplas_asignadas"):
            self.add_error("duplas_asignadas", "Seleccione al menos una dupla.")
        self._validate_selected_within_allowed(cleaned)
        cleaned = self._clean_pwa_fields(cleaned)
        cleaned = self._clean_territorial_comedor_fields(cleaned)
        cleaned = self._clean_relevador_calle_fields(cleaned)
        return self._validar_provincia_unica_coordinador(cleaned)

    def save(self, commit=True):
        with transaction.atomic():
            return self._save_atomic(commit=commit)

    def _save_atomic(  # pylint: disable=too-many-branches,too-many-statements
        self, commit=True
    ):
        new_pwd = self.cleaned_data.get("password")
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "")

        if new_pwd:
            user.set_password(new_pwd)
        else:
            user.password = self._original_password_hash

        is_pwa_operator = self._is_active_pwa_operator()
        is_pwa_read_only_coordinator = self.cleaned_data.get(
            "es_coordinador_equipo_tecnico_pwa", False
        )
        if (
            self.cleaned_data.get("es_representante_pwa", False)
            or is_pwa_read_only_coordinator
        ):
            user.is_staff = False
        elif self.cleaned_data.get("datacalle_rol") == "entrevistador":
            user.is_staff = False
        elif self.cleaned_data.get("es_coordinador", False):
            user.is_staff = True

        if commit:
            user.save()
            if is_pwa_read_only_coordinator:
                user.groups.clear()
                user.user_permissions.clear()
            elif self.cleaned_data.get("es_representante_pwa", False):
                user.groups.clear()
                pwa_permission_ids = (
                    self._preserve_current_pwa_operation_permission_ids(user)
                )
                user.user_permissions.clear()
                if pwa_permission_ids:
                    user.user_permissions.add(*pwa_permission_ids)
            else:
                pwa_permission_ids = (
                    self._preserve_current_pwa_operation_permission_ids(user)
                    if is_pwa_operator
                    else []
                )
                self._aplicar_grupos_y_permisos(user)
                self._sync_grupo_datacalle(user)
                if pwa_permission_ids:
                    user.user_permissions.add(*pwa_permission_ids)
            if not is_pwa_operator:
                self._sync_mobile_rendicion_permission(user)
            if self.cleaned_data.get("es_representante_pwa", False):
                self._sync_pwa_operation_permissions(user)

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.es_usuario_provincial = self.cleaned_data.get(
                "es_usuario_provincial", False
            )
            profile.dni = self.cleaned_data.get("dni", "")
            profile.cuil = self.cleaned_data.get("cuil", "")
            profile.tipo_usuario = self.cleaned_data["tipo_usuario"]
            profile.provincia = None
            profile.es_coordinador = self.cleaned_data.get("es_coordinador", False)
            profile.es_territorial_comedor = self.cleaned_data.get(
                "es_territorial_comedor", False
            )
            profile.es_relevador_calle = self.cleaned_data.get(
                "es_relevador_calle", False
            )
            profile.datacalle_rol = self.cleaned_data.get("datacalle_rol", "")
            profile.rol = self.cleaned_data.get("rol")
            if new_pwd:
                self._set_initial_password_flags(
                    profile,
                    must_change_password=True,
                    temporary_password_plaintext=None,
                    password_reset_requested_at=None,
                )
            elif (
                not self.cleaned_data.get("es_representante_pwa", False)
                and not is_pwa_read_only_coordinator
                and not is_pwa_operator
            ):
                profile.password_reset_requested_at = None
                profile.must_change_password = False
                profile.password_changed_at = None
                profile.initial_password_expires_at = timezone.now() + timedelta(
                    hours=settings.INITIAL_PASSWORD_MAX_AGE_HOURS
                )
                profile.temporary_password_plaintext = None
            profile.save()
            self._sync_territorial_comedor_provincias(profile)
            self._sync_relevador_calle_provincias(profile)
            sync_profile_territorial_scopes(
                profile,
                self.cleaned_data.get("territorial_scopes_data", []),
            )
            validar_alcance_coordinador(profile)
            user.refresh_from_db()
            profile.grupos_asignables.set(
                self.cleaned_data.get("grupos_asignables", [])
            )
            profile.roles_asignables.set(self.cleaned_data.get("roles_asignables", []))

            duplas = self.cleaned_data.get("duplas_asignadas", [])
            if profile.es_coordinador and duplas:
                profile.duplas_asignadas.set(duplas)
            else:
                profile.duplas_asignadas.clear()

            self._sync_pwa_access(user)

        return user


class GroupForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.select_related("content_type").order_by(
            "content_type__app_label", "name"
        ),
        required=False,
        widget=FilteredSelectMultiple("Permisos", is_stacked=False),
        label="Permisos (roles)",
        help_text=(
            "Selecciona los permisos del grupo. "
            "Estos permisos se aplican a todos los usuarios del grupo."
        ),
    )

    class Meta:
        model = Group
        fields = ["name", "permissions"]

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError("Este campo es obligatorio.")

        qs = Group.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe un grupo con ese nombre.")
        return name


class BulkCredentialsUploadForm(forms.Form):
    tipo_envio = forms.ChoiceField(
        label="Tipo de envio",
        choices=(),
        initial="standard",
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text="Seleccione el tipo de envio para descargar la plantilla correcta.",
    )
    archivo = forms.FileField(
        label="Archivo Excel",
        validators=[FileExtensionValidator(["xlsx"])],
        widget=forms.ClearableFileInput(attrs={"accept": ".xlsx"}),
        help_text="Cargue un archivo .xlsx con el formato esperado para el tipo de envio seleccionado.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipo_envio"].choices = get_bulk_credentials_send_type_choices()


class UserImportForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo Excel",
        validators=[FileExtensionValidator(["xlsx"])],
        widget=forms.ClearableFileInput(attrs={"accept": ".xlsx"}),
        help_text=(
            "Archivo .xlsx con columnas: Username, Nombre, Apellido, Correo, "
            "Permisos, Provincias, Rol, Organizaciones, Comedores."
        ),
    )
    enviar_credenciales = forms.BooleanField(
        label="Enviar credenciales por email",
        required=False,
        initial=True,
        help_text="Si esta marcado, se enviara un email con usuario y contrasena temporal a cada usuario creado.",
    )
    es_pwa = forms.BooleanField(
        label="Usuarios de la PWA",
        required=False,
        initial=False,
        help_text="Los usuarios importados son usuarios de la app movil (PWA).",
    )


# Leyenda del checkbox de declaración. Es la redacción provisoria acordada con
# UX/UI: queda pendiente de un filtro de aprobación posterior, así que puede
# volver con cambios. Para modificarla alcanza con esta constante; no hay copia
# duplicada en templates ni en tests.
#
# El texto original de UX estaba redactado como aviso en segunda persona
# ("comprometiéndote a..."), que no funciona como leyenda de un checkbox: al
class MiCuentaForm(forms.ModelForm):
    """Edición de los datos personales del propio usuario.

    Se comparte entre la vista persistente "Mi cuenta" y la confirmación
    obligatoria de primer ingreso, para que ambas apliquen exactamente la
    misma validación y el mismo guardado.

    A diferencia de ``CustomUserChangeForm``, acá no se exponen grupos,
    permisos, alcances territoriales ni delegación: el usuario solo edita sus
    propios datos identificatorios. ``tipo_usuario`` y ``rol`` quedan fuera a
    pedido de UX/UI: son datos de administración y el usuario final no los
    toca.

    Todos los campos son obligatorios salvo ``correo_institucional``.
    """

    dni = forms.CharField(
        max_length=16,
        label="DNI",
        help_text="Solo números, sin puntos.",
        error_messages={"required": "Ingrese su DNI."},
    )
    cuil = forms.CharField(
        max_length=16,
        label="CUIL",
        help_text="11 dígitos, con o sin guiones.",
        error_messages={"required": "Ingrese su CUIL."},
    )
    correo_institucional = forms.EmailField(
        required=False,
        label="Correo institucional",
        help_text="Opcional.",
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Mail",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre in ("first_name", "last_name", "email"):
            self.fields[nombre].required = True
        # Hay usuarios históricos sin perfil; el form igual debe poder abrirse.
        profile = get_profile_or_none(self.instance)
        if profile:
            self.fields["dni"].initial = profile.dni
            self.fields["cuil"].initial = profile.cuil
            self.fields["correo_institucional"].initial = profile.correo_institucional

    def clean_dni(self):
        dni = solo_digitos(self.cleaned_data.get("dni"))
        if len(dni) < 6:
            raise forms.ValidationError("Ingrese un DNI válido (solo números).")
        return dni

    def clean_cuil(self):
        return validate_cuit((self.cleaned_data.get("cuil") or "").strip())

    def clean_email(self):
        # El mail es obligatorio en este formulario pero sigue sin ser único:
        # la unicidad vive en username.
        return (self.cleaned_data.get("email") or "").strip()

    def save(self, commit=True):
        if not commit:
            raise ValueError("MiCuentaForm requiere commit=True para ser atómico.")
        with transaction.atomic():
            user = super().save(commit=True)
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.dni = self.cleaned_data["dni"]
            profile.cuil = self.cleaned_data["cuil"]
            profile.correo_institucional = self.cleaned_data["correo_institucional"]
            profile.needs_profile_confirmation = False
            profile.datos_confirmados_at = timezone.now()
            profile.save(
                update_fields=[
                    "dni",
                    "cuil",
                    "correo_institucional",
                    "needs_profile_confirmation",
                    "datos_confirmados_at",
                ]
            )
        return user

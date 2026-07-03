from django.contrib import admin

from ocr.models import OCRJob, OCRJobDocument


class OCRJobDocumentInline(admin.TabularInline):
    model = OCRJobDocument
    extra = 0
    readonly_fields = (
        "original_filename",
        "file_size",
        "status",
        "page_count",
        "error_message",
        "processed_at",
    )
    fields = (
        "original_filename",
        "file_size",
        "status",
        "page_count",
        "error_message",
        "processed_at",
    )
    can_delete = False


@admin.register(OCRJob)
class OCRJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "requested_by",
        "status",
        "total_documents",
        "processed_documents",
        "failed_documents",
        "requested_at",
        "finished_at",
    )
    list_filter = ("status",)
    readonly_fields = (
        "requested_by",
        "status",
        "total_documents",
        "processed_documents",
        "failed_documents",
        "last_error_message",
        "requested_at",
        "started_at",
        "finished_at",
        "last_activity_at",
    )
    inlines = [OCRJobDocumentInline]


@admin.register(OCRJobDocument)
class OCRJobDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "job",
        "original_filename",
        "status",
        "page_count",
        "processed_at",
    )
    list_filter = ("status",)
    readonly_fields = (
        "job",
        "original_filename",
        "file_size",
        "status",
        "page_count",
        "error_message",
        "processed_at",
    )

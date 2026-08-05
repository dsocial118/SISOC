(() => {
    const source = document.querySelector('[data-template-editor-source]');
    if (!source) {
        return;
    }

    const form = source.closest('form');
    const buscador = document.getElementById('buscar-variable-template');
    const variables = document.querySelectorAll('[data-template-variable]');
    const jquery = window.jQuery;
    const expresionVariable = /{{\s*[A-Za-z_][A-Za-z0-9_.]*\s*}}/g;
    const expresionVariableCompleta = /^\s*{{\s*[A-Za-z_][A-Za-z0-9_.]*\s*}}\s*$/;
    const etiquetasPermitidas = new Set([
        'a', 'b', 'blockquote', 'br', 'div', 'em', 'h1', 'h2', 'h3', 'h4',
        'h5', 'h6', 'hr', 'i', 'li', 'ol', 'p', 'pre', 's', 'span', 'strike',
        'strong', 'table', 'tbody', 'td', 'th', 'thead', 'tr', 'u', 'ul'
    ]);
    const etiquetasDescartadas = new Set([
        'embed', 'iframe', 'math', 'object', 'script', 'style', 'svg', 'template'
    ]);
    const tokensDisponibles = new Set(
        [...variables].map((variable) => variable.dataset.templateVariable)
    );
    let rangoGuardado = null;

    const esUrlSegura = (valor) => {
        try {
            const url = new URL(valor.trim());
            return ['http:', 'https:', 'mailto:'].includes(url.protocol);
        } catch (_) {
            return false;
        }
    };

    const limpiarEstilos = (valor) => valor.split(';').reduce((estilos, declaracion) => {
        const [propiedad, ...valores] = declaracion.split(':');
        const nombre = (propiedad || '').trim().toLowerCase();
        const contenido = valores.join(':').trim().toLowerCase();
        const colorValido = /^(?:#[0-9a-f]{3,8}|rgba?\([\d\s.,%]+\)|[a-z]+)$/i.test(
            contenido
        );
        if (
            nombre === 'text-align'
            && ['left', 'right', 'center', 'justify'].includes(contenido)
        ) {
            estilos.push(`${nombre}: ${contenido}`);
        } else if (['background-color', 'color'].includes(nombre) && colorValido) {
            estilos.push(`${nombre}: ${contenido}`);
        }
        return estilos;
    }, []).join('; ');

    const limpiarContenidoEditor = (contenido) => {
        const documento = new DOMParser().parseFromString(contenido || '', 'text/html');
        documento.body.querySelectorAll('*').forEach((elemento) => {
            const etiqueta = elemento.tagName.toLowerCase();
            if (etiquetasDescartadas.has(etiqueta)) {
                elemento.remove();
                return;
            }
            if (!etiquetasPermitidas.has(etiqueta)) {
                elemento.replaceWith(...elemento.childNodes);
                return;
            }
            [...elemento.attributes].forEach((atributo) => {
                const nombre = atributo.name.toLowerCase();
                const valor = atributo.value;
                const esAtributoDeTabla = ['td', 'th'].includes(etiqueta)
                    && ['colspan', 'rowspan'].includes(nombre)
                    && /^\d+$/.test(valor)
                    && Number(valor) > 0
                    && Number(valor) <= 100;
                const permitido = nombre === 'style'
                    || (etiqueta === 'a' && nombre === 'title')
                    || (etiqueta === 'a' && nombre === 'href' && esUrlSegura(valor))
                    || esAtributoDeTabla;
                if (!permitido) {
                    elemento.removeAttribute(atributo.name);
                }
            });
            if (elemento.hasAttribute('style')) {
                const estilos = limpiarEstilos(elemento.getAttribute('style'));
                if (estilos) {
                    elemento.setAttribute('style', estilos);
                } else {
                    elemento.removeAttribute('style');
                }
            }
        });
        return documento.body.innerHTML;
    };

    const desenvolverTokensPlanos = (contenedor) => {
        contenedor.querySelectorAll('span:not([data-template-token])').forEach((etiqueta) => {
            if (etiqueta.attributes.length === 0 && expresionVariableCompleta.test(etiqueta.textContent)) {
                etiqueta.replaceWith(contenedor.ownerDocument.createTextNode(etiqueta.textContent));
            }
        });
    };

    const convertirTokensEnEtiquetas = (contenido) => {
        const documento = new DOMParser().parseFromString(contenido, 'text/html');
        desenvolverTokensPlanos(documento.body);
        const nodosTexto = [];
        const explorador = documento.createTreeWalker(
            documento.body,
            NodeFilter.SHOW_TEXT
        );
        let nodo;
        while ((nodo = explorador.nextNode())) {
            if (!nodo.parentElement.closest('[data-template-token]')) {
                nodosTexto.push(nodo);
            }
        }
        nodosTexto.forEach((nodoTexto) => {
            const valor = nodoTexto.nodeValue;
            expresionVariable.lastIndex = 0;
            if (!expresionVariable.test(valor)) {
                return;
            }
            expresionVariable.lastIndex = 0;
            const fragmento = documento.createDocumentFragment();
            let cursor = 0;
            valor.replace(expresionVariable, (token, indice) => {
                fragmento.append(valor.slice(cursor, indice));
                const etiqueta = documento.createElement('span');
                etiqueta.className = 'gt-template-token';
                etiqueta.contentEditable = 'false';
                etiqueta.dataset.templateToken = token;
                etiqueta.textContent = token;
                fragmento.append(etiqueta, documento.createTextNode(' '));
                cursor = indice + token.length;
                return token;
            });
            fragmento.append(valor.slice(cursor));
            nodoTexto.replaceWith(fragmento);
        });
        return documento.body.innerHTML;
    };

    const serializarContenido = (contenido) => {
        const documento = new DOMParser().parseFromString(contenido || '', 'text/html');
        documento.body.querySelectorAll('[data-template-token]').forEach((etiqueta) => {
            etiqueta.replaceWith(
                documento.createTextNode(etiqueta.dataset.templateToken || etiqueta.textContent)
            );
        });
        desenvolverTokensPlanos(documento.body);
        return limpiarContenidoEditor(documento.body.innerHTML);
    };

    const insertarEnTextarea = (token) => {
        const inicio = source.selectionStart;
        const fin = source.selectionEnd;
        source.value = source.value.slice(0, inicio) + token + source.value.slice(fin);
        const proximaPosicion = inicio + token.length;
        source.focus();
        source.setSelectionRange(proximaPosicion, proximaPosicion);
        source.dispatchEvent(new Event('input', {bubbles: true}));
    };

    if (!jquery || !jquery.fn.summernote) {
        variables.forEach((variable) => {
            variable.addEventListener('click', () => {
                insertarEnTextarea(variable.dataset.templateVariable);
            });
            variable.addEventListener('dragstart', (evento) => {
                evento.dataTransfer.effectAllowed = 'copy';
                evento.dataTransfer.setData('text/plain', variable.dataset.templateVariable);
            });
        });
        source.addEventListener('dragover', (evento) => {
            evento.preventDefault();
            evento.dataTransfer.dropEffect = 'copy';
        });
        source.addEventListener('drop', (evento) => {
            const token = evento.dataTransfer.getData('text/plain');
            if (!tokensDisponibles.has(token)) {
                return;
            }
            evento.preventDefault();
            insertarEnTextarea(token);
        });
    } else {
        const $source = jquery(source);
        const sincronizarFuente = () => {
            source.value = serializarContenido($source.summernote('code'));
        };
        source.value = limpiarContenidoEditor(source.value);
        $source.summernote({
            height: 460,
            minHeight: 280,
            dialogsInBody: true,
            disableDragAndDrop: true,
            placeholder: 'Escribí el contenido del informe técnico…',
            toolbar: [
                ['historial', ['undo', 'redo']],
                ['estilo', ['style']],
                ['formato', ['bold', 'italic', 'underline', 'clear']],
                ['color', ['color']],
                ['párrafo', ['ul', 'ol', 'paragraph']],
                ['insertar', ['table', 'link', 'hr']],
                ['vista', ['codeview', 'fullscreen']]
            ],
            styleTags: ['p', 'blockquote', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
            callbacks: {
                onChange: (contenido) => {
                    rangoGuardado = $source.summernote('createRange');
                    window.setTimeout(sincronizarFuente, 0);
                },
                onPaste: (evento) => {
                    const portapapeles = evento.originalEvent.clipboardData || window.clipboardData;
                    const texto = portapapeles && portapapeles.getData('text/plain');
                    if (!texto) {
                        return;
                    }
                    evento.preventDefault();
                    document.execCommand('insertText', false, texto);
                }
            }
        });

        $source.summernote('code', convertirTokensEnEtiquetas(source.value));
        sincronizarFuente();
        const $editor = $source.next('.note-editor');
        const $areaEdicion = $editor.find('.note-editable');

        const etiquetasHerramientas = [
            [/^Undo/, 'Deshacer (Ctrl+Z)'],
            [/^Redo/, 'Rehacer (Ctrl+Y)'],
            [/^Style$/, 'Estilos de párrafo'],
            [/^Bold/, 'Negrita (Ctrl+B)'],
            [/^Italic/, 'Cursiva (Ctrl+I)'],
            [/^Underline/, 'Subrayado (Ctrl+U)'],
            [/^Remove Font Style/, 'Quitar formato'],
            [/^Recent Color/, 'Aplicar el último color de fondo'],
            [/^More Color/, 'Elegir color de fondo o texto'],
            [/^Unordered list/, 'Lista con viñetas'],
            [/^Ordered list/, 'Lista numerada'],
            [/^Paragraph$/, 'Alineación y sangría'],
            [/^Align left/, 'Alinear a la izquierda'],
            [/^Align center/, 'Centrar'],
            [/^Align right/, 'Alinear a la derecha'],
            [/^Justify full/, 'Justificar'],
            [/^Outdent/, 'Reducir sangría'],
            [/^Indent/, 'Aumentar sangría'],
            [/^Table$/, 'Insertar tabla'],
            [/^Link/, 'Insertar enlace (Ctrl+K)'],
            [/^Insert Horizontal Rule/, 'Insertar separador'],
            [/^Code View/, 'Editar HTML'],
            [/^Full Screen/, 'Pantalla completa']
        ];

        const traducirHerramientas = () => {
            $editor.find('.note-btn').each((_, boton) => {
                const etiquetaActual = boton.getAttribute('aria-label') || boton.title || '';
                const coincidencia = etiquetasHerramientas.find(([patron]) => patron.test(etiquetaActual));
                const etiqueta = coincidencia ? coincidencia[1] : boton.dataset.gtTooltip;
                if (!etiqueta) {
                    return;
                }
                boton.dataset.gtTooltip = etiqueta;
                boton.title = etiqueta;
                boton.setAttribute('aria-label', etiqueta);
            });
        };

        const cerrarMenusDesplegables = (menuAConservar = null) => {
            $editor.find('.note-dropdown-menu.show').each((_, menu) => {
                if (menu !== menuAConservar) {
                    menu.classList.remove('show');
                    const boton = menu.parentElement.querySelector('.note-btn[data-toggle="dropdown"]');
                    if (boton) {
                        boton.classList.remove('show');
                        boton.setAttribute('aria-expanded', 'false');
                    }
                }
            });
        };

        const alternarMenuDesplegable = (boton) => {
            const grupo = boton.closest('.note-btn-group');
            const menu = grupo && grupo.querySelector('.note-dropdown-menu');
            if (!menu) {
                return;
            }
            const seAbrira = !menu.classList.contains('show');
            cerrarMenusDesplegables(seAbrira ? menu : null);
            menu.classList.toggle('show', seAbrira);
            boton.classList.toggle('show', seAbrira);
            boton.setAttribute('aria-expanded', String(seAbrira));
        };

        traducirHerramientas();
        $editor.on('click', '.note-btn[data-toggle="dropdown"]', (evento) => {
            evento.preventDefault();
            evento.stopPropagation();
            alternarMenuDesplegable(evento.currentTarget);
            window.setTimeout(traducirHerramientas, 0);
        });
        $editor.on('click', '.note-dropdown-menu button, .note-dropdown-menu a', () => {
            window.setTimeout(cerrarMenusDesplegables, 0);
        });
        $editor.on('mousedown', '.note-dropdown-menu [data-event]', () => {
            if (rangoGuardado) {
                rangoGuardado.select();
            }
        });
        jquery(document).on('click.gestorTemplatesEditor', (evento) => {
            if (!$editor.get(0).contains(evento.target)) {
                cerrarMenusDesplegables();
            }
        });
        jquery(document).on('keydown.gestorTemplatesEditor', (evento) => {
            if (evento.key === 'Escape') {
                cerrarMenusDesplegables();
            }
        });

        const guardarRango = () => {
            if (!$source.summernote('codeview.isActivated')) {
                rangoGuardado = $source.summernote('createRange');
            }
        };
        $areaEdicion.on('keyup mouseup focus', guardarRango);
        $source.on('summernote.codeview.toggled', () => {
            if (!$source.summernote('codeview.isActivated')) {
                const contenidoSeguro = limpiarContenidoEditor($source.summernote('code'));
                $source.summernote('code', convertirTokensEnEtiquetas(contenidoSeguro));
                window.setTimeout(sincronizarFuente, 0);
            }
            traducirHerramientas();
        });

        const insertar = (token) => {
            if ($source.summernote('codeview.isActivated')) {
                const areaCodigo = $editor.find('.note-codable').get(0);
                const inicio = areaCodigo.selectionStart;
                const fin = areaCodigo.selectionEnd;
                areaCodigo.value = areaCodigo.value.slice(0, inicio)
                    + token + areaCodigo.value.slice(fin);
                const posicion = inicio + token.length;
                areaCodigo.focus();
                areaCodigo.setSelectionRange(posicion, posicion);
                areaCodigo.dispatchEvent(new Event('input', {bubbles: true}));
                window.setTimeout(sincronizarFuente, 0);
                return;
            }
            $source.summernote('focus');
            if (rangoGuardado) {
                rangoGuardado.select();
            }
            const etiqueta = document.createElement('span');
            etiqueta.className = 'gt-template-token';
            etiqueta.contentEditable = 'false';
            etiqueta.dataset.templateToken = token;
            etiqueta.textContent = token;
            $source.summernote('insertNode', etiqueta);
            $source.summernote('insertText', ' ');
            sincronizarFuente();
            guardarRango();
        };

        variables.forEach((variable) => {
            variable.addEventListener('click', () => insertar(variable.dataset.templateVariable));
            variable.addEventListener('dragstart', (evento) => {
                evento.dataTransfer.effectAllowed = 'copy';
                evento.dataTransfer.setData('text/plain', variable.dataset.templateVariable);
            });
        });

        $areaEdicion.on('dragover', (evento) => {
            evento.preventDefault();
            evento.originalEvent.dataTransfer.dropEffect = 'copy';
        });
        $areaEdicion.on('drop', (evento) => {
            const token = evento.originalEvent.dataTransfer.getData('text/plain');
            if (!tokensDisponibles.has(token)) {
                return;
            }
            evento.preventDefault();
            const rango = document.caretRangeFromPoint && document.caretRangeFromPoint(
                evento.originalEvent.clientX,
                evento.originalEvent.clientY
            );
            if (rango) {
                const seleccion = window.getSelection();
                seleccion.removeAllRanges();
                seleccion.addRange(rango);
                guardarRango();
            }
            insertar(token);
        });

        form.addEventListener('submit', () => {
            sincronizarFuente();
        });
    }

    buscador.addEventListener('input', () => {
        const termino = buscador.value.trim().toLowerCase();
        variables.forEach((variable) => {
            variable.hidden = termino && !variable.dataset.variableSearch.includes(termino);
        });
        document.querySelectorAll('[data-categoria-variable]').forEach((categoria) => {
            categoria.hidden = ![...categoria.querySelectorAll('[data-template-variable]')]
                .some((variable) => !variable.hidden);
        });
    });
})();

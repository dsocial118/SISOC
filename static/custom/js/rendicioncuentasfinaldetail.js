
document.addEventListener('DOMContentLoaded', function () {
    const modalAdjuntarDocumentoRendicionFinal = document.getElementById('modalAdjuntarDocumentoRendicionFinal')
    modalAdjuntarDocumentoRendicionFinal.addEventListener('show.bs.modal', event => {
        const button = event.relatedTarget
        const docId = button.getAttribute('data-doc-id')
        const docTipo = button.getAttribute('data-doc-tipo')

        const inputDocId = modalAdjuntarDocumentoRendicionFinal.querySelector('#documento_id')
        const tipoTexto = modalAdjuntarDocumentoRendicionFinal.querySelector('#tipoDocumentoTexto')

        inputDocId.value = docId
        tipoTexto.textContent = `Documento: ${docTipo}`
    })

    const modal = document.getElementById('modal-observaciones');
    const modalTitle = document.getElementById('modal-observaciones-label');
    const modalBody = document.getElementById('modal-observaciones-body');

    document.querySelectorAll('.ver-observaciones').forEach(btn => {
        btn.addEventListener('click', function () {
            const observaciones = this.getAttribute('data-observaciones');
            const titulo = this.getAttribute('data-titulo');
            modalTitle.textContent = titulo || 'Observaciones';
            modalBody.textContent = observaciones || 'Sin observaciones';
        });
    });
});
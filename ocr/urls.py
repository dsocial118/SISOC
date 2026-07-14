from django.urls import path

from ocr.views import OCRDocumentDownloadView, OCRJobDetailView, OCRUploadView

urlpatterns = [
    path("", OCRUploadView.as_view(), name="ocr_upload"),
    path("<int:pk>/", OCRJobDetailView.as_view(), name="ocr_job_detail"),
    path(
        "documentos/<int:doc_pk>/descargar/",
        OCRDocumentDownloadView.as_view(),
        name="ocr_document_download",
    ),
]

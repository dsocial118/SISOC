"""
Comando de evaluación de calidad del OCR.

Procesa un archivo (imagen o PDF) con el pipeline real de SISOC y compara el
texto extraído contra un ground-truth, reportando recall/precision/F1 de
palabras. Útil para medir el impacto de cambios en el preprocesado o en la
configuración de Tesseract (antes/después).

No incluye documentos de prueba: el archivo y el ground-truth se pasan por
argumento (pueden contener datos personales, no deben versionarse).

Ejemplos:
    python manage.py ocr_eval --file doc.pdf --ground-truth ref.txt
    python manage.py ocr_eval --file doc.pdf --ground-truth ref.txt --no-preprocess
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ocr.eval_metrics import word_recall
from ocr.services_ocr import extract_text_from_file


class Command(BaseCommand):
    help = "Evalúa el OCR comparando el texto extraído contra un ground-truth."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file", required=True, help="Ruta al PDF o imagen a procesar."
        )
        parser.add_argument(
            "--ground-truth",
            required=True,
            help="Ruta a un .txt con el texto de referencia.",
        )
        parser.add_argument(
            "--language",
            default=None,
            help="Código de idioma Tesseract (default: setting OCR_LANGUAGE).",
        )
        parser.add_argument(
            "--no-preprocess",
            action="store_true",
            help="Desactiva el preprocesado OpenCV para esta corrida (compara baseline).",
        )
        parser.add_argument(
            "--show-text",
            action="store_true",
            help="Imprime el texto extraído completo.",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"])
        gt_path = Path(options["ground_truth"])
        if not file_path.exists():
            raise CommandError(f"No existe el archivo: {file_path}")
        if not gt_path.exists():
            raise CommandError(f"No existe el ground-truth: {gt_path}")

        if options["no_preprocess"]:
            settings.OCR_PREPROCESS = False

        result = extract_text_from_file(
            str(file_path), file_path.name, options["language"]
        )
        extracted = result["text"]
        ground_truth = gt_path.read_text(encoding="utf-8")
        metrics = word_recall(extracted, ground_truth)

        preprocess = getattr(settings, "OCR_PREPROCESS", True)
        self.stdout.write(f"archivo         : {file_path.name}")
        self.stdout.write(f"preprocesado    : {preprocess}")
        self.stdout.write(f"paginas         : {result.get('page_count')}")
        self.stdout.write(f"chars extraidos : {len(extracted)}")
        self.stdout.write(f"recall          : {metrics['recall']:.3f}")
        self.stdout.write(f"precision       : {metrics['precision']:.3f}")
        self.stdout.write(f"f1              : {metrics['f1']:.3f}")
        self.stdout.write(
            f"palabras match  : {metrics['matched']}/{metrics['gt_total']}"
        )
        if result.get("warning"):
            self.stdout.write(f"warning         : {result['warning']}")
        if options["show_text"]:
            self.stdout.write("----- TEXTO EXTRAIDO -----")
            self.stdout.write(extracted)

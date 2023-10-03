from haystack.telemetry import tutorial_running
from haystack.nodes import TextConverter, PDFToTextConverter, DocxToTextConverter, PreProcessor
import logging
from haystack.nodes import PreProcessor


# Logs
logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.WARNING)
logging.getLogger("haystack").setLevel(logging.INFO)


# all_docs = convert_files_to_docs(dir_path=doc_dir)

converter = TextConverter(remove_numeric_tables=True, valid_languages=["en"])
doc_txt = converter.convert(file_path="tesis-qa-system\prueba.txt", meta=None)[0]


preprocessor = PreProcessor(
    clean_empty_lines=True,
    clean_whitespace=True,
    clean_header_footer=False,
    split_by="word",
    split_length=100,
    split_respect_sentence_boundary=True,
)

docs_default = preprocessor.process([doc_txt])
print(f"n_docs_input: 1\nn_docs_output: {len(docs_default)}")






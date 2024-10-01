import time
import json

import pypdfium2 # Needs to be at the top to avoid warnings
import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1" # For some reason, transformers decided to use .isin for a simple op, which is not supported on MPS

import argparse
from marker.convert import convert_single_pdf
from marker.logger import configure_logging
from marker.models import load_all_models

from marker.output import save_markdown

configure_logging()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="PDF file to parse")
    parser.add_argument("output", help="Output base folder path")
    parser.add_argument("--max_pages", type=int, default=None, help="Maximum number of pages to parse")
    parser.add_argument("--start_page", type=int, default=None, help="Page to start processing at")
    parser.add_argument("--langs", type=str, help="Optional languages to use for OCR, comma separated", default=None)
    parser.add_argument("--batch_multiplier", type=int, default=2, help="How much to increase batch sizes")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging", default=False)
    parser.add_argument("--ocr_all_pages", action="store_true", help="Force OCR on all pages", default=False)
    parser.add_argument("--replace_tables", action="store_true", help="Replace tables with <<table id>>", default=False)
    parser.add_argument("--extract_tables", action="store_true", help="Extract tables out", default=False)
    args = parser.parse_args()

    langs = args.langs.split(",") if args.langs else None

    fname = args.filename
    model_lst = load_all_models()
    start = time.time()
    full_text, images, out_meta, table_md_list, table_coorinates = convert_single_pdf(
        fname, model_lst, max_pages=args.max_pages, langs=langs, batch_multiplier=args.batch_multiplier, start_page=args.start_page,
        ocr_all_pages=args.ocr_all_pages, replace_tables=args.replace_tables)

    fname = os.path.basename(fname)
    subfolder_path = save_markdown(args.output, fname, full_text, images, out_meta)

    # Save the tables if requested
    if args.extract_tables:
        for idx, table_md in enumerate(table_md_list):
            table_fname = f"{fname}_table_{idx}.md"
            with open(os.path.join(subfolder_path, table_fname), "w") as f:
                f.write(table_md)

        # Save the table coordinates
        for idx, table_text in enumerate(table_coorinates):
            table_fname = f"{fname}_table_{idx}.json"
            with open(os.path.join(subfolder_path, table_fname), "w") as f:
                jsonStr = json.dumps(table_text, indent=4)
                f.write(jsonStr)


    print(f"Saved markdown to the {subfolder_path} folder")
    if args.debug:
        print(f"Total time: {time.time() - start}")


if __name__ == "__main__":
    main()

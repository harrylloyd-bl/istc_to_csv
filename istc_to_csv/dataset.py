import logging
from pathlib import Path
import re
from typing import Tuple, Dict

import pandas as pd
from tqdm import tqdm
try:
    from yaml import load_all, CLoader as Loader
except ImportError:
    from yaml import load_all, Loader


from istc_to_csv.config import PROJ_ROOT, PROCESSED_DATA_DIR, RAW_DATA_DIR

logger = logging.getLogger(__name__)
logger.info(f"PROJ_ROOT path is: {PROJ_ROOT}")


def row_from_doc(doc: Dict) -> Tuple[Dict]:
    """
    Parse a YAML doc into flat csv rows
    The YAML doc is a (potentially nested) dictionary of strings describing a particular ISTC entry
    'history' field showing edit history omitted from core
    :param doc: Dict
    :return: Tuple[Dict]
    """
    holdings, imprints, references, notes, related_resources = {}, {}, {}, {}, {}

    core = {doc["_id"]: {
        "author": doc["data"].get("author", ""),
        'cataloguing_level': doc["data"].get("cataloguing_level", ""),
        'date_of_item_from': doc["data"].get("date_of_item_from", ""),
        'date_of_item_to': doc["data"].get("date_of_item_to", ""),
        'date_of_item_single_date': doc["data"].get("date_of_item_single_date", ""),
        'dimensions': doc["data"].get("dimensions", ""),
        'id_assigned_by': doc["data"].get("id_assigned_by", ""),
        'language_of_item': doc["data"].get("language_of_item", ""),
        'material_type': doc["data"].get("material_type", ""),
        'title': doc["data"].get("title", ""),
        'uncontrolled_term': doc["data"].get("uncontrolled_term", ""),
        'date_of_cataloguing': doc.get("meta", {}).get("date_of_cataloguing", "")
    }
    }

    if doc["data"].get("holdings", False):
        holdings = [{doc["_id"]: {
            'copy_note': holding.get("copy_note", ""),
            'country_code': holding.get("country_code", ""),
            'holding_institution_id': holding.get("holding_institution_id", ""),
            'holding_institution_name': holding.get("holding_institution_name", ""),
            'shelfmark': holding.get("shelf_mark", "")
        }} for holding in doc["data"]["holdings"]
        ]

    if doc["data"].get("imprint", False):
        imprints = [{doc["_id"]: {
            'geonames_id': imprint.get("geo_info", [{}])[0].get("geonames_id", ""),
            'imprint_country_code': imprint.get("geo_info", [{}])[0].get("imprint_country_code", ""),
            'lat': imprint.get("geo_info", [{}])[0].get("lat", ""),
            'lon': imprint.get("geo_info", [{}])[0].get("lon", ""),
            'imprint_date': imprint.get("imprint_date", ""),
            'imprint_name': imprint.get("imprint_name", ""),
            'imprint_place': imprint.get("imprint_place", "")
        }} for imprint in doc["data"]["imprint"]
        ]

    if doc["data"].get("references", False):
        references = [{doc["_id"]: {
            'reference_location_in_source': reference.get("reference_location_in_source", ""),
            'reference_name': reference.get("reference_name", "")
        }} for reference in doc["data"]["references"]
        ]

    if doc["data"].get("notes", False):
        notes = [{doc["_id"]: note} for note in doc["data"]["notes"]]

    if doc["data"].get("related_resources", False):
        related_resources = [{doc["_id"]: {
            'resource_name': resource.get("resource_name", ""),
            'resource_type': resource.get("resource_type", ""),
            'resource_url': resource.get("resource_url", "")
        }} for resource in doc["data"]["related_resources"]
        ]

    return core, holdings, imprints, references, notes, related_resources


def main(
    input_path: Path = RAW_DATA_DIR / "istc.yaml",
    output_path: Path = PROCESSED_DATA_DIR,
):
    logging.basicConfig(filename="yaml_to_csv.log", level=logging.INFO)
    logger.info("Processing dataset...")
    print("Loading and cleaning YAML")
    with open(input_path, "r", encoding="utf8") as f:
        istc_with_enc_errors = f.read()
        # there are a few encoding errors in the raw data that need to be fixed
        istc_clean = istc_with_enc_errors.replace("\x81", "ü").replace("\x92", "Æ").replace("\x9a", "Ü")

    istc_entries = []
    for doc in tqdm(load_all(istc_clean, Loader=Loader), total=len(istc_clean.split("---")[1:])):
        istc_entries.append(doc)

    print("Parsing YAML to different dataframes")
    rows = [row_from_doc(d) for d in istc_entries]
    core = [r[0] for r in rows]
    holdings = [r[1] for r in rows]
    imprints = [r[2] for r in rows]
    references = [r[3] for r in rows]
    notes = [r[4] for r in rows]
    related_resources = [r[5] for r in rows]

    complete_dfs = {}

    print("Creating core (non-repeating) dataframe")
    core_no_notes_df = pd.DataFrame(data=[list(c.values())[0] for c in core], index=[list(c.keys())[0] for c in core])
    notes_idx_raw = [[list(d) for d in work_entry] for work_entry in notes if work_entry]
    notes_idx = pd.Index([x[0] for x in pd.Series(notes_idx_raw).sum()])

    notes_vals_raw = [[list(d.values()) for d in work_entry] for work_entry in notes if work_entry]
    notes_vals_stacked = pd.Series(notes_vals_raw)
    notes_df = pd.Series([x[0] for x in notes_vals_stacked.sum()], index=notes_idx)
    # combine repeat notes with ;; as described in data dictionary
    combined_notes = (notes_df + ";;").groupby(by=notes_df.index).sum().str.rstrip(";;").rename("notes")

    core_df = core_no_notes_df.join(combined_notes, how="left")

    woodcut_idx = notes_df[notes_df.str.contains("woodcut", flags=re.IGNORECASE)].index.unique()
    woodcut = pd.Series(False, index=core_df.index)
    woodcut.loc[woodcut_idx] = True
    core_df["woodcut"] = woodcut

    # no woodcuts created from entries missing a notes field
    assert len(core_df["notes"][core_df["woodcut"]].dropna()) == woodcut.sum()
    complete_dfs["core"] = core_df

    print("Creating non-core (repeating) dataframes")
    for name, series in {"holdings": holdings, "imprints": imprints, "references": references,
                         "related_resources": related_resources}.items():
        print(f"Processing {name}")
        flat_entries = []
        for i in series:
            [flat_entries.append(j) for j in i]

        flat_labelled_entries = {}
        for i, fi in enumerate(flat_entries):
            reffed_d = list(fi.values())[0]
            reffed_d["istc_no"] = list(fi.keys())[0]
            flat_labelled_entries[i] = reffed_d

        series_df = pd.DataFrame.from_dict(flat_labelled_entries, orient='index').set_index("istc_no")
        complete_dfs[name] = series_df

    print("Creating core/holdings and core/imprints dataframes")
    complete_dfs["core_holdings"] = core_df.join(complete_dfs["holdings"], how="left")
    complete_dfs["core_imprints"] = core_df.join(complete_dfs["imprints"], how="left")

    print("Exporting processed dataframes")
    for k, v in complete_dfs.items():
        print(f"{k}")
        v.to_csv(output_path / f"{k}.csv", encoding="utf8", index=True)

    print("Processing dataset complete")
    logger.info("Processing dataset complete.")


if __name__ == "__main__":
    main()

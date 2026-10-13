"""
Convert extracted Unicode Devanagari text from g1_extr.pdf or g2.pdf into hierarchical JSON:
Hierarchy: Parva -> Prapataka -> Kandah -> Samam (with Checksum for each Samam).
"""

import argparse
import json
import re
from pathlib import Path
from extract_g1_unicode import extract_pages_unicode


DEVA_DIGITS = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
               '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}
INT_TO_DEVA = {v: k for k, v in DEVA_DIGITS.items()}


def deva_to_int(s: str):
    if not s:
        return None
    s_clean = s.strip()
    if s_clean == "नास्ति":
        return 0
    ascii_s = ''.join(DEVA_DIGITS.get(c, c) for c in s_clean)
    try:
        return int(ascii_s)
    except ValueError:
        return None


def int_to_deva(n: int) -> str:
    return ''.join(INT_TO_DEVA.get(c, c) for c in str(n))


def parse_header_name_and_meta(rest: str):
    """
    Splits Samam header text after '१।१।' into (samam_name, metadata).
    Example: 'पर्कः।गोतमो, गायत्री अग्निः॥' -> ('पर्कः', 'गोतमो, गायत्री अग्निः')
    """
    if not rest:
        return "", ""
    cleaned = re.sub(r'[।॥\s]+$', '', rest).strip()
    m = re.split(r'[।॥]+', cleaned, maxsplit=1)
    if len(m) == 2:
        return m[0].strip(), m[1].strip()
    return cleaned, ""


def parse_checksum_line(line: str, fallback_variant_num: int = 1):
    """
    Parses a Samam checksum line (both Page 1 'दीर्घाः ...' format and standard '(दी॰ ...)' format,
    including print variations such as 'नास्ति', omitted 'मा॰', or range numbers like '११९४ - ११९५').
    Returns a dict or None if the line is not a checksum line.
    """
    if line.startswith("दीर्घाः"):
        m = re.match(
            r'^दीर्घाः\s*([०-९]+)\s*।\s*पर्वाणि\s*([०-९]+)\s*।\s*मात्राः\s*([०-९]+)\s*'
            r'॥\s*([^॥]+?)\s*॥\s*([०-९]+)\s*॥$',
            line,
        )
        if not m:
            return None
        d_val, p_val, m_val, code_val, g_val = m.groups()
        k_num = int_to_deva(fallback_variant_num)
        return {
            "raw": line,
            "dirghah": d_val,
            "parvani": p_val,
            "matrah": m_val,
            "dirghah_int": deva_to_int(d_val),
            "parvani_int": deva_to_int(p_val),
            "matrah_int": deva_to_int(m_val),
            "prapataka_samam_num": k_num,
            "prapataka_samam_num_int": fallback_variant_num,
            "code": code_val.strip(),
            "global_samam_num": g_val,
            "global_samam_num_int": deva_to_int(g_val),
        }

    if not line.startswith("(दी॰"):
        return None

    d_m = re.search(r'दी॰\s*([०-९\s]+|नास्ति)', line)
    p_m = re.search(r'प॰\s*([०-९\s]+|नास्ति)', line)
    m_m = re.search(r'मा॰\s*([०-९\s]+|नास्ति)?', line)
    k_m = re.search(r'\)\s*\(?([०-९]+)\)?', line)
    g_m = re.search(r'([०-९]+(?:\s*-\s*[०-९]+)?)\s*॥\s*$', line)

    c_m = re.search(r'॥\s*([^॥०-९\s()][^॥०-९()]*?)\s*(?:॥|\)|\s+[०-९])', line)
    if not c_m:
        c_m = re.search(r'\)\s*([^॥०-९\s()][^॥०-९()]*?)\s*॥', line)

    d_val = d_m.group(1).replace(" ", "") if d_m else ""
    p_val = p_m.group(1).replace(" ", "") if p_m else ""
    m_val = (m_m.group(1) or "").replace(" ", "") if m_m else ""
    k_num = k_m.group(1).strip() if k_m else ""
    code_val = c_m.group(1).strip() if c_m else ""
    g_val = g_m.group(1).strip() if g_m else ""

    return {
        "raw": line,
        "dirghah": d_val,
        "parvani": p_val,
        "matrah": m_val,
        "dirghah_int": deva_to_int(d_val),
        "parvani_int": deva_to_int(p_val),
        "matrah_int": deva_to_int(m_val),
        "prapataka_samam_num": k_num,
        "prapataka_samam_num_int": deva_to_int(k_num),
        "code": code_val,
        "global_samam_num": g_val,
        "global_samam_num_int": deva_to_int(g_val.split("-")[0]) if g_val else None,
    }


def build_g1_json(pages_data, source_pdf_str="pdfconverter/data/input/g1_extr.pdf"):
    invocations = []
    parvas = []

    current_parva = None
    current_prapataka = None
    current_kandah = None
    current_samam = None
    pending_kandah_title = None
    kandah_counter = 0
    prapataka_counter = 0
    gramageya_finished = False

    samam_hdr_re = re.compile(r'^([०-९]+)।([०-९]+)।\s*(.*)$')
    swara_or_chant_re = re.compile(r'[\uA8E0-\uA8FF\u1CD0-\u1CFF]|ऽ[०-९]')

    def clean_toc_heading(text: str) -> str:
        t = str(text).replace("॥", "").strip()
        t = t.replace("अथैन्द्रं", "ऐन्द्रं")
        t = re.sub(r"(^|\.\s+)अथ\s+", r"\1", t)
        return t.strip()

    def start_parva(title: str):
        nonlocal current_parva
        current_parva = {
            "parva_id": len(parvas) + 1,
            "parva_title": title,
            "parva_title_toc": clean_toc_heading(title),
            "prapatakas": [],
        }
        parvas.append(current_parva)
        return current_parva

    def ensure_parva(title="॥ १. आग्नेयं पर्व ॥"):
        if current_parva is None:
            return start_parva(title)
        return current_parva

    def start_prapataka(title, is_intro=False):
        nonlocal current_prapataka, current_kandah, prapataka_counter
        ensure_parva()
        if is_intro:
            pid = "0"
        else:
            prapataka_counter += 1
            pid = str(prapataka_counter)
        current_prapataka = {
            "prapataka_id": pid,
            "prapataka_title": title,
            "prapataka_title_toc": clean_toc_heading(title),
            "colophon": "",
            "kandahs": [],
        }
        current_parva["prapatakas"].append(current_prapataka)
        current_kandah = None
        return current_prapataka

    def start_kandah(title, is_intro=False, is_continuation=False):
        nonlocal current_kandah, kandah_counter
        if current_prapataka is None:
            start_prapataka("प्रकृतिगानम् (गायत्रम्)", is_intro=True)
        if is_intro:
            kid = "0"
        elif is_continuation:
            kid = f"{kandah_counter}_cont"
        else:
            kandah_counter += 1
            kid = str(kandah_counter)
        current_kandah = {
            "kandah_id": kid,
            "kandah_title": title,
            "kandah_title_toc": clean_toc_heading(title),
            "colophon": "",
            "samam_count": 0,
            "samams": [],
        }
        current_prapataka["kandahs"].append(current_kandah)
        return current_kandah

    for p in pages_data:
        if gramageya_finished:
            break
        page_num = p["page"]
        lines = p["lines"]

        for line in lines:
            # Stop once the Gramageyaganam text concludes (before Appendix / Suchi table)
            if "इति ग्राम-गेयगानं समाप्तम्" in line or "ग्रामगेय-गानानां प्रपाठकानुसरेण सूची" in line or line == "A P P E N D I X":
                if "इति ग्राम-गेयगानं समाप्तम्" in line and current_prapataka:
                    current_prapataka["colophon"] = (
                        f"{current_prapataka['colophon']} | {line}".strip(" |")
                        if current_prapataka["colophon"] else line
                    )
                gramageya_finished = True
                break

            # 1. Page 1 invocations & Parva title
            if page_num == 1 and current_parva is None:
                if "पर्व" in line and line.startswith("॥"):
                    ensure_parva(line.replace("पर्व॥", "पर्व ॥"))
                    continue
                else:
                    invocations.append(line)
                    continue

            # 2. Page 1 Gayatram intro headers
            if page_num == 1 and line.startswith("गायत्रम् ।"):
                start_prapataka("॥ अथ प्रकृतिगानम् (गायत्रम्) ॥", is_intro=True)
                start_kandah("॥ गायत्रम् ॥", is_intro=True)
                name, meta = parse_header_name_and_meta(line)
                current_samam = {
                    "samam_id": "०-१",
                    "samam_id_ascii": "0-1",
                    "rik_num": 0,
                    "variant_num": 1,
                    "header": line,
                    "header_title": f"{name}।",
                    "toc_title": name,
                    "name": name,
                    "metadata": meta,
                    "mantra_lines": [],
                    "mantra_text": "",
                    "checksum": None,
                    "page": page_num,
                }
                current_kandah["samams"].append(current_samam)
                current_kandah["samam_count"] = len(current_kandah["samams"])
                continue

            if page_num == 1 and line == "Version 2":
                current_samam = {
                    "samam_id": "०-२",
                    "samam_id_ascii": "0-2",
                    "rik_num": 0,
                    "variant_num": 2,
                    "header": "गायत्रम् (पाठान्तरम् / Version 2) । परमेष्ठी प्रजापतिः, गायत्री, सविता ॥",
                    "header_title": "गायत्रम् (Version 2)।",
                    "toc_title": "गायत्रम् (Version 2)",
                    "name": "गायत्रम् (Version 2)",
                    "metadata": "परमेष्ठी प्रजापतिः, गायत्री, सविता",
                    "mantra_lines": [],
                    "mantra_text": "",
                    "checksum": None,
                    "page": page_num,
                }
                current_kandah["samams"].append(current_samam)
                current_kandah["samam_count"] = len(current_kandah["samams"])
                continue

            if page_num == 1 and line.startswith("इति प्रकृतिसप्तगानान्तर्भूतं"):
                if current_prapataka:
                    current_prapataka["colophon"] = line
                current_samam = None
                continue

            # 3. Checksum lines (Page 1 format & Standard/Variant formats)
            ck_parsed = parse_checksum_line(
                line,
                fallback_variant_num=(current_samam["variant_num"] if current_samam else 1),
            )
            if ck_parsed and current_samam is not None:
                current_samam["mantra_text"] = "\n".join(current_samam["mantra_lines"])
                current_samam["checksum"] = ck_parsed
                current_samam = None
                continue

            # 4. Structural Headers & Colophons (lines starting with ॥)
            if line.startswith("॥"):
                # Parva 2 start: ॥ अथैन्द्रं पर्व॥
                if "अथैन्द्रं पर्व" in line:
                    start_parva("॥ २. अथैन्द्रं पर्व ॥")
                    current_prapataka = None
                    current_kandah = None
                    current_samam = None
                    continue

                # Parva 3 start: ॥ अथ पावमानं काण्डम् ॥
                if "अथ पावमानं काण्डम्" in line:
                    start_parva("॥ ३. अथ पावमानं पर्व (काण्डम्) ॥")
                    current_prapataka = None
                    current_kandah = None
                    current_samam = None
                    continue

                # Prapathaka start: e.g. ॥ अथ प्रथमप्रपाठके प्रथमोऽर्द्धः ॥
                if "प्रपाठके" in line and "अथ" in line:
                    prev_kandah_title = (
                        current_kandah["kandah_title"]
                        if (current_kandah and not current_kandah["colophon"])
                        else None
                    )
                    start_prapataka(line)
                    if pending_kandah_title:
                        start_kandah(pending_kandah_title)
                        pending_kandah_title = None
                    elif prev_kandah_title:
                        clean_prev = (
                            prev_kandah_title.strip("॥ ")
                            .replace("अथ ", "")
                            .replace(" (उत्तरभागः)", "")
                            .strip()
                        )
                        start_kandah(f"॥ {clean_prev} (उत्तरभागः) ॥", is_continuation=True)
                    continue

                # Prapathaka / Parva colophon: e.g. ॥ इति ग्रामे गेय-गाने प्रथमः प्रपाठकः ॥ १ ॥
                if "इति" in line and ("प्रपाठकः" in line or "प्रपाथकः" in line or "पर्व" in line or "काण्डम्" in line or "अध्यायः" in line or "गानं समाप्तम्" in line or "तन्त्रं समाप्तम्" in line or "ककुभुष्णिहः" in line):
                    if current_prapataka:
                        current_prapataka["colophon"] = (
                            f"{current_prapataka['colophon']} | {line}".strip(" |")
                            if current_prapataka["colophon"] else line
                        )
                    continue

                # Ignore standalone chapter sub-label like ॥ पञ्चमोऽध्यायः॥
                if "अध्यायः" in line and "अथ" not in line:
                    continue

                # Kandah start: e.g. ॥ अथ प्रथम खण्डः ॥
                if "अथ" in line and "खण्डः" in line:
                    if current_kandah is not None and len(current_kandah["samams"]) == 0:
                        current_kandah["kandah_title"] = line
                        current_kandah["kandah_title_toc"] = clean_toc_heading(line)
                    elif current_prapataka is not None and len(current_prapataka["kandahs"]) > 0 and current_prapataka["colophon"]:
                        pending_kandah_title = line
                    else:
                        start_kandah(line)
                    continue

                # Kandah / Dashati colophon: e.g. ॥ एकोनविंशतिः । प्रथमः खण्डः ॥ १ ॥ or ॥ पञ्चमी दशतिः ॥ ५ ॥
                if ("खण्डः" in line or "दशति" in line) and "अथ" not in line:
                    if current_kandah:
                        current_kandah["colophon"] = (
                            f"{current_kandah['colophon']} | {line}".strip(" |")
                            if current_kandah["colophon"] else line
                        )
                    continue

            # 5. Samam Header: e.g. १।१। पर्कः।गोतमो, गायत्री अग्निः॥
            m_sh = samam_hdr_re.match(line)
            if m_sh:
                # Handle missing Prapathaka 5 Ardha 1 header on Page 94 of g2.pdf (after चतुर्थः प्रपाठकः colophon)
                if current_prapataka and "चतुर्थः प्रपाठकः" in current_prapataka.get("colophon", ""):
                    start_prapataka("॥ अथ पञ्चमप्रपाठके प्रथमोऽर्द्धः ॥")
                    if pending_kandah_title:
                        start_kandah(pending_kandah_title)
                        pending_kandah_title = None
                    else:
                        start_kandah("॥ अथ प्रथमो खण्डः ॥")
                elif pending_kandah_title:
                    start_kandah(pending_kandah_title)
                    pending_kandah_title = None
                elif current_kandah is None or current_kandah.get("colophon"):
                    next_k_idx = len(current_prapataka["kandahs"]) + 1 if current_prapataka else 1
                    start_kandah(f"॥ अथ खण्डः ({int_to_deva(next_k_idx)}) ॥")

                r_deva, v_deva, rest = m_sh.groups()
                r_int = deva_to_int(r_deva)
                v_int = deva_to_int(v_deva)
                name, meta = parse_header_name_and_meta(rest)

                samam_id_deva = f"{r_deva}-{v_deva}"
                header_title = f"{samam_id_deva} {name}।" if name else samam_id_deva
                toc_title = f"{samam_id_deva} {name}" if name else samam_id_deva
                formatted_header = f"{samam_id_deva} {rest}".strip() if rest else samam_id_deva

                current_samam = {
                    "samam_id": samam_id_deva,
                    "samam_id_ascii": f"{r_int}-{v_int}",
                    "rik_num": r_int,
                    "variant_num": v_int,
                    " _raw_rest": rest,
                    "header": formatted_header,
                    "header_title": header_title,
                    "toc_title": toc_title,
                    "name": name,
                    "metadata": meta,
                    "mantra_lines": [],
                    "mantra_text": "",
                    "checksum": None,
                    "page": page_num,
                }
                current_kandah["samams"].append(current_samam)
                current_kandah["samam_count"] = len(current_kandah["samams"])
                continue

            # 6. Mantra chant line (or wrapped 2nd line of Samam header) belonging to current_samam
            if current_samam is not None:
                raw_rest = current_samam.get(" _raw_rest", "")
                if (
                    len(current_samam["mantra_lines"]) == 0
                    and raw_rest
                    and not raw_rest.endswith("॥")
                    and not swara_or_chant_re.search(line)
                ):
                    # Wrapped continuation of Samam header (e.g. 'गायत्रीन्द्रः॥' on next line)
                    combined_rest = f"{raw_rest} {line}".strip()
                    current_samam[" _raw_rest"] = combined_rest
                    name, meta = parse_header_name_and_meta(combined_rest)
                    sid = current_samam["samam_id"]
                    current_samam["name"] = name
                    current_samam["metadata"] = meta
                    current_samam["header"] = f"{sid} {combined_rest}".strip()
                    current_samam["header_title"] = f"{sid} {name}।" if name else sid
                    current_samam["toc_title"] = f"{sid} {name}" if name else sid
                else:
                    current_samam.pop(" _raw_rest", None)
                    current_samam["mantra_lines"].append(line)

    # Clean up any temporary key if left on last samam
    for pv in parvas:
        for pr in pv["prapatakas"]:
            for k in pr["kandahs"]:
                for s in k["samams"]:
                    s.pop(" _raw_rest", None)

    # Compute totals
    total_prapatakas = sum(len(pv["prapatakas"]) for pv in parvas)
    total_kandahs = sum(len(pr["kandahs"]) for pv in parvas for pr in pv["prapatakas"])
    total_samams = sum(len(k["samams"]) for pv in parvas for pr in pv["prapatakas"] for k in pr["kandahs"])

    result = {
        "meta": {
            "title": "ग्रामेगेयगानम् (प्रकृतिगानम्)",
            "invocations": invocations,
            "source_pdf": source_pdf_str,
            "hierarchy": ["Parva", "Prapataka", "Kandah", "Samam"],
            "total_parvas": len(parvas),
            "total_prapatakas": total_prapatakas,
            "total_kandahs": total_kandahs,
            "total_samams": total_samams,
        },
        "parvas": parvas,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="Convert g1_extr.pdf or g2.pdf to Parva->Prapataka->Kandah->Samam JSON")
    parser.add_argument(
        "--input-pdf", "-i",
        default="pdfconverter/data/input/g1_extr.pdf",
        help="Path to input PDF file",
    )
    parser.add_argument(
        "--output-txt", "-t",
        default="pdfconverter/data/output/g1_extr_unicode.txt",
        help="Path to output extracted Unicode text file",
    )
    parser.add_argument(
        "--output-json", "-o",
        default="pdfconverter/data/output/g1_extr.json",
        help="Path to output hierarchical JSON file",
    )
    args = parser.parse_args()

    pdf_path = Path(args.input_pdf)
    txt_path = Path(args.output_txt)
    json_path = Path(args.output_json)

    txt_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    pages_data = extract_pages_unicode(pdf_path)

    # Save Unicode text file
    out_lines = []
    for p in pages_data:
        out_lines.append(f"--- Page {p['page']} ---")
        out_lines.extend(p["lines"])
        out_lines.append("")
    txt_path.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"[OK] Saved extracted Unicode text to {txt_path}")

    # Build and save hierarchical JSON
    data = build_g1_json(pages_data, source_pdf_str=str(pdf_path).replace("\\", "/"))
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"[OK] Saved hierarchical JSON to {json_path} "
        f"(Parvas={data['meta']['total_parvas']}, "
        f"Prapatakas={data['meta']['total_prapatakas']}, "
        f"Kandahs={data['meta']['total_kandahs']}, "
        f"Samams={data['meta']['total_samams']})"
    )


if __name__ == "__main__":
    main()

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from src.malayalam.ml_transliterate import (
    normalize_deva_vowels_native,
    malayalam_to_devanagari,
    malayalam_to_devanagari_mantra_line,
    convert_malayalam_data_to_devanagari,
)

def test_normalize_deva_vowels_native():
    assert normalize_deva_vowels_native("नॊ_") == "नो_"
    assert normalize_deva_vowels_native("नाइहॊ_") == "नाइहो_"
    assert normalize_deva_vowels_native("आग्नॆयपाठः") == "आग्नेयपाठः"
    assert normalize_deva_vowels_native("गृणा(चा) नॊ_(श)") == "गृणा(चा) नो_(श)"
    assert normalize_deva_vowels_native("ऎहि ऒम्") == "एहि ओम्"
    assert normalize_deva_vowels_native("जैमिनीय साम संहित") == "जैमिनीय साम संहिता"
    assert normalize_deva_vowels_native("जैमिनीय साम संहिता") == "जैमिनीय साम संहिता"
    assert normalize_deva_vowels_native("साम सूक्तमाल") == "साम सूक्तमाला"
    assert normalize_deva_vowels_native("साम सूक्तमाला") == "साम सूक्तमाला"
    print("PASS: test_normalize_deva_vowels_native")


def test_malayalam_to_devanagari_default_vs_preserve():
    # Default: Native Sanskrit (no hrsva)
    res_default = malayalam_to_devanagari("ആഗ്നെയപാഠഃ", preserve_hrsva=False)
    assert "ॆ" not in res_default
    assert "े" in res_default
    assert res_default == "आग्नेयपाठः"

    # Optional: preserve_hrsva=True
    res_hrsva = malayalam_to_devanagari("ആഗ്നെയപാഠഃ", preserve_hrsva=True)
    assert "ॆ" in res_hrsva
    assert res_hrsva == "आग्नॆयपाठः"
    print("PASS: test_malayalam_to_devanagari_default_vs_preserve")


def test_malayalam_to_devanagari_mantra_line():
    sample_mal = "ഗൃണാ(𑌚𑌾) നൊ_(𑌶) ഹവ്യാ_ദാ(𑌚𑌿)(|) । നാഇഹൊ_(𑌕𑌿) താ(𑌚)(|) । ഔഹൊവാ(𑌶𑌿)"
    
    # Default (preserve_hrsva=False)
    res_default = malayalam_to_devanagari_mantra_line(sample_mal, preserve_hrsva=False)
    assert "ॊ" not in res_default
    assert "नो_" in res_default
    assert "नाइहो_" in res_default
    assert "औहोवा" in res_default

    # Optional (preserve_hrsva=True)
    res_hrsva = malayalam_to_devanagari_mantra_line(sample_mal, preserve_hrsva=True)
    assert "ॊ" in res_hrsva
    assert "नॊ_" in res_hrsva
    assert "नाइहॊ_" in res_hrsva
    assert "औहॊവാ" not in res_hrsva
    assert "औहॊवा" in res_hrsva
    print("PASS: test_malayalam_to_devanagari_mantra_line")


def test_convert_malayalam_data_to_devanagari():
    data = {
        "supersection": {
            "supersection_1": {
                "supersection_title": "ആഗ്നെയപാഠഃ",
                "sections": {
                    "section_1": {
                        "section_title": "പ്രഥമ ഖണ്ഡഃ",
                        "subsections": {
                            "subsection_1": {
                                "header": {"header": "॥ഗൗതമസ്യപൎക്കഃ॥"},
                                "malayalam-mantra-sets": [
                                    {"malayalam-mantra": "ഗൃണാ(𑌚𑌾) നൊ_(𑌶) । നാഇഹൊ_(𑌕𑌿)"}
                                ]
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Default
    deva_default = convert_malayalam_data_to_devanagari(data, preserve_hrsva=False)
    super_title = deva_default["supersection"]["supersection_1"]["supersection_title"]
    mantra = deva_default["supersection"]["supersection_1"]["sections"]["section_1"]["subsections"]["subsection_1"]["corrected-mantra_sets"][0]["corrected-mantra"]
    assert "ॆ" not in super_title
    assert "ॊ" not in mantra
    assert super_title == "आग्नेयपाठः"
    assert "नो_" in mantra
    assert "नाइहो_" in mantra

    # With preserve_hrsva=True
    deva_hrsva = convert_malayalam_data_to_devanagari(data, preserve_hrsva=True)
    super_title_h = deva_hrsva["supersection"]["supersection_1"]["supersection_title"]
    mantra_h = deva_hrsva["supersection"]["supersection_1"]["sections"]["section_1"]["subsections"]["subsection_1"]["corrected-mantra_sets"][0]["corrected-mantra"]
    assert "ॆ" in super_title_h
    assert "ॊ" in mantra_h
    assert super_title_h == "आग्नॆयपाठः"
    assert "नॊ_" in mantra_h
    print("PASS: test_convert_malayalam_data_to_devanagari")

if __name__ == "__main__":
    test_normalize_deva_vowels_native()
    test_malayalam_to_devanagari_default_vs_preserve()
    test_malayalam_to_devanagari_mantra_line()
    test_convert_malayalam_data_to_devanagari()
    print("\nALL TESTS PASSED SUCCESSFULLY!")

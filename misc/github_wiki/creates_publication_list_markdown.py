"""Creates markdown github wiki from bibtex files.

Use this version of pybtex for this code to work as expected: https://bitbucket.org/aurelienjaquier/pybtex/src/custom-style/
"""

import re
from pathlib import Path

from pybtex import PybtexEngine

from pybtex.style.formatting.unsrt import Style as OriginalStyle
from pybtex.style.template import field, sentence, tag


class Style(OriginalStyle):
    """Style similar to unsrt, but with bold titles and sorting by date."""
    default_sorting_style = 'year_month' # must have custom pybtex to use this

    def format_title(self, e, which_field, as_sentence=True):
        formatted_title = field(
            which_field, apply_func=lambda text: text.capitalize()
        )
        formatted_title = tag('b') [ formatted_title ]
        if as_sentence:
            return sentence [ formatted_title ]
        else:
            return formatted_title


def put_bullet_points(input):
    """Replace references by bullet points."""
    to_replace = "\[[0-9]+\]"  # any numbers in braquets
    return re.sub(to_replace, "*", input)


working_directory = Path("./")
bibtex_folder = working_directory / "bibtex"
output_path = working_directory / "output" / "gh_wiki.md"

uses_BPO = bibtex_folder / "uses_BPO.bib" # from zotero
uses_BPO_extra = bibtex_folder / "uses_BPO_extra.bib" # extra custom
mentions_BPO = bibtex_folder / "mentions_BPO.bib"
mentions_BPO_extra = bibtex_folder / "mentions_BPO_extra.bib"
thesis_uses_BPO = bibtex_folder / "thesis_uses_BPO.bib"
thesis_mentions_BPO = bibtex_folder / "thesis_mentions_BPO.bib"
poster_uses_BPO = bibtex_folder / "poster_uses_BPO.bib"


# style should have number references for them to be replaced later by regex
# e.g. "unsrt"
style = Style

# -- turn bibtex files into markdown -- #
engine = PybtexEngine()

md_uses_bpo = engine.format_from_files(
    [uses_BPO, uses_BPO_extra], style=style, output_backend="markdown"
)
md_mentions_bpo = engine.format_from_files(
    [mentions_BPO, mentions_BPO_extra], style=style, output_backend="markdown"
)
md_thesis_uses_BPO = engine.format_from_file(
    thesis_uses_BPO, style=style, output_backend="markdown"
)
md_thesis_mentions_BPO = engine.format_from_file(
    thesis_mentions_BPO, style=style, output_backend="markdown"
)
md_poster_uses_BPO = engine.format_from_file(
    poster_uses_BPO, style=style, output_backend="markdown"
)

# -- replace references by bullet points -- #
md_uses_bpo = put_bullet_points(md_uses_bpo)
md_mentions_bpo = put_bullet_points(md_mentions_bpo)
md_thesis_uses_BPO = put_bullet_points(md_thesis_uses_BPO)
md_thesis_mentions_BPO = put_bullet_points(md_thesis_mentions_BPO)
md_poster_uses_BPO = put_bullet_points(md_poster_uses_BPO)

# -- assemble markdown parts into one markdown wiki -- #
output = f"""# Publications that use or mention BluePyOpt


## Scientific papers that use BluePyOpt
{md_uses_bpo}

## Scientific papers that mention BluePyOpt
{md_mentions_bpo}

## Theses that use BluePyOpt
{md_thesis_uses_BPO}

## Theses that mention BluePyOpt
{md_thesis_mentions_BPO}

## Posters that use BluePyOpt
{md_poster_uses_BPO}
"""


# -- write down markdown wiki -- #
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w") as f:
    f.write(output)

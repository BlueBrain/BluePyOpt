"""Creates markdown github wiki from bibtex files."""

import re
from pathlib import Path

from pybtex import PybtexEngine

def put_bullet_points(input):
    """Replace references by bullet points."""
    to_replace = "\[[0-9]+\]" # any numbers in braquets
    return re.sub(to_replace, "*", input)

working_directory = Path("./")
bibtex_folder = working_directory / "bibtex"
output_path = working_directory / "output" / "gh_wiki.md"

# style should have number references for them to be replaced later by regex
# e.g. unsrt
style = "unsrt"

# -- turn bibtex files into markdown -- #
engine = PybtexEngine()
# bibtex from zotero
md_use_bpo = engine.format_from_file(
    bibtex_folder / "uses_BPO.bib", style=style, output_backend="markdown"
)
# bibtex custom (bibtex output from paper not good)
md_use_bpo_extra = engine.format_from_file(
    bibtex_folder / "uses_BPO_extra.bib", style=style, output_backend="markdown"
)

# bibtex from zotero
md_mentions_bpo = engine.format_from_file(
    bibtex_folder / "mentions_BPO.bib", style=style, output_backend="markdown"
)
# bibtex custom (bibtex output from paper not good)
md_mentions_bpo_extra = engine.format_from_file(
    bibtex_folder / "mentions_BPO_extra.bib", style=style, output_backend="markdown"
)

# thesis (custom bibtex)
md_thesis_uses_BPO = engine.format_from_file(
    bibtex_folder / "thesis_uses_BPO.bib", style=style, output_backend="markdown"
)
md_thesis_mentions_BPO = engine.format_from_file(
    bibtex_folder / "thesis_mentions_BPO.bib", style=style, output_backend="markdown"
)

# poster (custom bibtex)
md_poster_uses_BPO = engine.format_from_file(
    bibtex_folder / "poster_uses_BPO.bib", style=style, output_backend="markdown"
)

# -- replace references by bullet points -- #
md_use_bpo = put_bullet_points(md_use_bpo)
md_use_bpo_extra = put_bullet_points(md_use_bpo_extra)
md_mentions_bpo = put_bullet_points(md_mentions_bpo)
md_mentions_bpo_extra = put_bullet_points(md_mentions_bpo_extra)
md_thesis_uses_BPO = put_bullet_points(md_thesis_uses_BPO)
md_thesis_mentions_BPO = put_bullet_points(md_thesis_mentions_BPO)
md_poster_uses_BPO = put_bullet_points(md_poster_uses_BPO)

# -- assemble markdown parts into one markdown wiki -- #
output = f"""# Publications that use or mention BluePyOpt


## Scientific papers that use BluePyOpt
{md_use_bpo}{md_use_bpo_extra}

## Scientific papers that mention BluePyOpt
{md_mentions_bpo}{md_mentions_bpo_extra}

## Theses that use BluePyOpt
{md_thesis_uses_BPO}

## Theses that mention BluePyOpt
{md_thesis_mentions_BPO}

## Posters that use BluePyOpt
{md_poster_uses_BPO}
"""


# -- write down markwodn wiki -- #
with open(output_path, "w") as f:
    f.write(output)

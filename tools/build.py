#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建 md-print-pdf.html：tpl-oss.html + marked.min.js + 可选的两枚徽章。

用法：
    # 不带徽章（默认）
    python tools/build.py

    # 加上自己的校徽 / 徽章
    python tools/build.py --main 校徽.png --secondary 徽章.png

    # 指定输出
    python tools/build.py --main my-crest.png -o /path/to/md-print-pdf.html

参数：
    --main       主徽章 PNG，页眉左上角，实渲 14mm（建议透明底正方形，边长 ≥ 600px）
    --secondary  次徽章 PNG，主徽章右侧，实渲 12mm
"""
import argparse
import base64
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
DEFAULT_TPL = ROOT / "tpl-oss.html"
DEFAULT_MARKED = TOOLS / "marked.min.js"


def load_b64(p: pathlib.Path) -> str:
    raw = p.read_bytes()
    if not raw.startswith(b"\x89PNG"):
        sys.exit("!! %s 不是 PNG 文件（按 PNG 规范应以此魔数开头）" % p.name)
    return base64.b64encode(raw).decode("ascii")


def main() -> None:
    ap = argparse.ArgumentParser(description="构建 md-print-pdf.html")
    ap.add_argument("--main", metavar="PNG", help="主徽章（页眉左上角，实渲 14mm）")
    ap.add_argument("--secondary", metavar="PNG", help="次徽章（主徽章右侧，实渲 12mm）")
    ap.add_argument("--tpl", default=str(DEFAULT_TPL), help="模板文件，默认 tpl-oss.html")
    ap.add_argument("-o", "--out", default=str(ROOT / "md-print-pdf.html"), help="输出路径")
    a = ap.parse_args()

    tpl_path = pathlib.Path(a.tpl)
    if not tpl_path.exists():
        sys.exit("!! 找不到模板：%s" % tpl_path)
    tpl = tpl_path.read_text(encoding="utf-8-sig")

    marked_path = DEFAULT_MARKED
    if not marked_path.exists():
        sys.exit("!! 找不到 marked.min.js（应位于 %s）" % marked_path)
    marked = marked_path.read_text(encoding="utf-8")
    # 防止内嵌脚本里出现 </script> 或 <!-- 提前截断宿主 HTML
    marked = marked.replace("<!--", "<\\!--").replace("</script", "<\\/script")

    out = tpl.replace("/*__MARKED_SRC__*/", marked)
    assert "/*__MARKED_SRC__*/" not in out, "marked 占位符未替换"

    n_crest = 0
    if a.main:
        out = out.replace("var CREST_SRC = '';",
                          "var CREST_SRC = 'data:image/png;base64," + load_b64(pathlib.Path(a.main)) + "';")
        assert "var CREST_SRC = '';" not in out, "主徽章占位符未替换"
        n_crest += 1
    if a.secondary:
        out = out.replace("var CREST2_SRC = '';",
                          "var CREST2_SRC = 'data:image/png;base64," + load_b64(pathlib.Path(a.secondary)) + "';")
        assert "var CREST2_SRC = '';" not in out, "次徽章占位符未替换"
        n_crest += 1

    # 完整性自检
    for need in ("function paginate", "function setPageTitle", "function buildTOC", "buildPageShell"):
        assert need in out, "产物缺少 %s" % need
    assert "__MARKED_SRC__" not in out and "__CREST_B64__" not in out, "占位符残留"

    outp = pathlib.Path(a.out)
    outp.write_text(out, encoding="utf-8-sig")
    print("OK  已生成 %s" % outp)
    print("    体积 %.1f KB   徽章 %d 枚" % (outp.stat().st_size / 1024, n_crest))
    if n_crest == 0:
        print("    提示：未指定徽章，页眉只显示文档标题。加徽章用 --main / --secondary")


if __name__ == "__main__":
    main()

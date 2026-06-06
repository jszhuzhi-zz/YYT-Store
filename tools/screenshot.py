#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 Playwright(Chromium) 把原型各页面截图到 screenshots/。

依赖：pip install playwright && python -m playwright install chromium
运行：python tools/screenshot.py
说明：以 file:// 打开，前端自动回退本地示例数据；若想截「实时数据」版，
     先启动后端(见 backend/README)，把 base 改为 http://127.0.0.1:8000/ui/。
"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROTO = ROOT / "prototype"
OUT = ROOT / "screenshots"; OUT.mkdir(exist_ok=True)
url = lambda f: (PROTO / f).as_uri()


def clip_of(pg, sel, m=18):
    b = pg.query_selector(sel).bounding_box()
    return {"x": b["x"] - m, "y": b["y"] - m, "width": b["width"] + 2 * m, "height": b["height"] + 2 * m}


def main():
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 470, "height": 940}, device_scale_factor=2)
        pg.goto(url("index.html")); pg.wait_for_timeout(700)

        def shot(n):
            pg.wait_for_timeout(450)
            pg.screenshot(path=str(OUT / n), clip=clip_of(pg, ".phone"))
            print("saved", n)

        shot("01-mobile-工作台.png")
        pg.click('.nav .t[data-s="check"]'); shot("02-mobile-体检.png")
        pg.click('.nav .t[data-s="ai"]'); shot("03-mobile-AI问数.png")
        pg.click('#ai .seg .o[data-v="data"]'); shot("04-mobile-数据查询.png")
        pg.click('.nav .t[data-s="grow"]'); shot("05-mobile-增长.png")
        pg.close()

        pg2 = br.new_page(viewport={"width": 1340, "height": 900}, device_scale_factor=2)
        pg2.goto(url("dashboard.html")); pg2.wait_for_timeout(700)
        pg2.screenshot(path=str(OUT / "06-dashboard-集团驾驶舱.png"), full_page=True)
        print("saved 06-dashboard-集团驾驶舱.png")
        br.close()


if __name__ == "__main__":
    main()

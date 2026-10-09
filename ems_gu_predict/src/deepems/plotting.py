"""matplotlib 공용 설정 — analyze.py/visualize.py가 같이 쓴다.

Agg 백엔드(화면 없는 환경에서도 동작)와 한글 폰트 탐색을 한 곳에만
둬서, 두 모듈이 서로 다르게 설정해 그래프 스타일이 어긋나는 일이
없게 한다.
"""
from __future__ import annotations


def get_plt():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.font_manager as fm
    import matplotlib.pyplot as plt

    # 한글 라벨(제목/범례)이 그래프에 네모(missing glyph)로 깨져 나오지 않도록,
    # 시스템에 있는 한글 폰트를 찾아 우선순위로 지정한다. 없는 환경(리눅스 CI 등)
    # 에서는 조용히 기본 폰트로 넘어간다 — 한글이 깨질 뿐 그래프 생성 자체는 된다.
    for name in ("Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR"):
        if any(f.name == name for f in fm.fontManager.ttflist):
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False  # 한글 폰트 사용 시 마이너스 기호 깨짐 방지

    return plt


def small_multiples_grid(plt, n: int, ncols: int, subplot_w: float, subplot_h: float):
    """n개 서브플롯을 ncols열 그리드로 배치한 fig/axes를 만든다. 남는 칸은
    호출부에서 axis("off")로 꺼야 한다 — analyze.py/visualize.py가 태그별로
    작은 서브플롯을 나란히 그릴 때 공유해서 쓴다."""
    nrows = -(-n // ncols)  # ceil
    fig, axes = plt.subplots(nrows, ncols, figsize=(subplot_w * ncols, subplot_h * nrows), squeeze=False)
    return fig, axes, nrows, ncols

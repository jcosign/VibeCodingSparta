"""local_model.py - 로컬 AI 함수 3종(API 키 불필요, CPU에서 동작).

- classify_image(image, top_k=5)  : ViT-Tiny로 이미지 분류 (D1)
- generate_image(prompt, ...)     : 경량 Diffusion(segmind/tiny-sd)으로 이미지 생성 (D2)
- load_sample_airpassengers()     : AirPassengers 샘플 시계열 불러오기 (D3)
- forecast_timeseries(ts, ...)    : Holt-Winters(ExponentialSmoothing)로 미래 값 예측 (D4)

모델은 처음 호출할 때 한 번만 내려받아 메모리에 올리고(lru_cache), 이후 호출에서는 그대로 재사용합니다.
"모델 로드는 한 번, 추론은 여러 번"(D2 4-5)이 기본 원칙입니다.
"""
import time
from functools import lru_cache

import numpy as np
import pandas as pd

VIT_MODEL_ID = "WinKawaks/vit-tiny-patch16-224"   # D1: ViT-Tiny(약 570만 파라미터), ImageNet 1,000종
DIFFUSION_MODEL_ID = "segmind/tiny-sd"              # D2: 지식증류 경량 모델(디스크 약 1GB)

# AirPassengers(1949-01 ~ 1960-12, 월별 국제선 승객 수, 단위 천 명) - Box & Jenkins(1976)
# 인터넷이 안 될 때 쓰는 백업 데이터입니다(D3 예제와 같은 방식).
_AIRPASSENGERS = [
    112, 118, 132, 129, 121, 135, 148, 148, 136, 119, 104, 118,  # 1949
    115, 126, 141, 135, 125, 149, 170, 170, 158, 133, 114, 140,  # 1950
    145, 150, 178, 163, 172, 178, 199, 199, 184, 162, 146, 166,  # 1951
    171, 180, 193, 181, 183, 218, 230, 242, 209, 191, 172, 194,  # 1952
    196, 196, 236, 235, 229, 243, 264, 272, 237, 211, 180, 201,  # 1953
    204, 188, 235, 227, 234, 264, 302, 293, 259, 229, 203, 229,  # 1954
    242, 233, 267, 269, 270, 315, 364, 347, 312, 274, 237, 278,  # 1955
    284, 277, 317, 313, 318, 374, 413, 405, 355, 306, 271, 306,  # 1956
    315, 301, 356, 348, 355, 422, 465, 467, 404, 347, 305, 336,  # 1957
    340, 318, 362, 348, 363, 435, 491, 505, 404, 359, 310, 337,  # 1958
    360, 342, 406, 396, 420, 472, 548, 559, 463, 407, 362, 405,  # 1959
    417, 391, 419, 461, 472, 535, 622, 606, 508, 461, 390, 432,  # 1960
]


# ─────────────────────────────── D1: 이미지 분류(ViT) ───────────────────────────────
@lru_cache(maxsize=1)
def _load_vit():
    """ViT-Tiny 모델과 전처리기를 한 번만 불러와 캐싱합니다(두 번째 호출부터는 즉시 반환)."""
    from transformers import AutoImageProcessor, AutoModelForImageClassification

    processor = AutoImageProcessor.from_pretrained(VIT_MODEL_ID)
    model = AutoModelForImageClassification.from_pretrained(VIT_MODEL_ID)
    model.eval()
    return processor, model


def classify_image(image, top_k=5):
    """이미지 1장을 분류해 Top-k 라벨과 확신도(%)를 DataFrame으로 돌려줍니다.

    image: PIL.Image 또는 (H, W, 3) numpy 배열(D1: "이미지는 숫자 격자")
    """
    import torch
    from PIL import Image

    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    image = image.convert("RGB")             # 흑백·RGBA 이미지도 RGB 3채널로 맞춤

    processor, model = _load_vit()
    inputs = processor(images=image, return_tensors="pt")   # 224×224로 맞춘 뒤 16×16 패치(196개)로 읽힘
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)[0]
    values, indices = torch.topk(probs, k=top_k)
    rows = [
        {"순위": rank, "라벨": model.config.id2label[int(idx)], "확신도(%)": round(float(val) * 100, 2)}
        for rank, (val, idx) in enumerate(zip(values, indices), start=1)
    ]
    return pd.DataFrame(rows)


# ─────────────────────────────── D2: 이미지 생성(Diffusion) ───────────────────────────────
@lru_cache(maxsize=1)
def _load_diffusion():
    """segmind/tiny-sd 파이프라인을 한 번만 불러와 캐싱합니다(최초 1회 약 1GB 다운로드)."""
    import torch
    from diffusers import StableDiffusionPipeline

    pipe = StableDiffusionPipeline.from_pretrained(
        DIFFUSION_MODEL_ID,
        torch_dtype=torch.float32,   # CPU에서는 float32
        safety_checker=None,         # 교육용 실습이라 끔. 실제 서비스에서는 반드시 켜거나 별도 필터 필요(D2 4-6)
    )
    pipe = pipe.to("cpu")
    pipe.set_progress_bar_config(disable=True)
    return pipe


def generate_image(prompt, steps=10, guidance_scale=7.0, seed=0, size=256):
    """프롬프트로 이미지 1장을 생성합니다. 반환: (PIL.Image, 생성시간 초).

    steps          : 디노이징 스텝 수(num_inference_steps). 많을수록 보통 품질↑ 시간↑
    guidance_scale : 프롬프트를 얼마나 강하게 따를지(7~8 부근이 흔한 시작점)
    seed           : 같은 프롬프트+같은 시드+같은 설정이면 같은 결과가 재현됨
    """
    import torch

    pipe = _load_diffusion()
    generator = torch.Generator(device="cpu").manual_seed(int(seed))
    start = time.perf_counter()
    result = pipe(
        prompt,
        num_inference_steps=int(steps),
        guidance_scale=float(guidance_scale),
        height=int(size),
        width=int(size),
        generator=generator,
    )
    elapsed = time.perf_counter() - start
    return result.images[0], elapsed


# ─────────────────────────────── D3: 시계열 샘플 데이터 ───────────────────────────────
def load_sample_airpassengers():
    """AirPassengers를 월초(MS) 날짜 인덱스를 가진 Series로 돌려줍니다.

    인터넷이 되면 statsmodels.datasets.get_rdataset으로 원본을 받고, 실패하면 백업 데이터를 씁니다.
    반환: (Series, 출처 설명 문자열)
    """
    try:
        import statsmodels.api as sm

        data = sm.datasets.get_rdataset("AirPassengers", "datasets")
        values = data.data["value"].astype(int).tolist()
        source = "statsmodels.datasets.get_rdataset (인터넷)"
    except Exception:
        values = list(_AIRPASSENGERS)
        source = "내장 백업 데이터 (오프라인)"
    index = pd.date_range("1949-01-01", periods=len(values), freq="MS")
    return pd.Series(values, index=index, name="passengers"), source


def series_from_csv(df):
    """업로드한 CSV(날짜·값 두 열)를 시간 순으로 정렬된 Series로 바꿉니다.

    첫 번째 열 = 날짜, 두 번째 열 = 값. 날짜 간격(빈도)을 자동 추정해 인덱스에 붙입니다.
    """
    if df.shape[1] < 2:
        raise ValueError("CSV에는 최소 2개 열(날짜, 값)이 있어야 합니다.")
    dates = pd.to_datetime(df.iloc[:, 0], errors="coerce")
    values = pd.to_numeric(df.iloc[:, 1], errors="coerce")
    ts = pd.Series(values.values, index=dates, name=str(df.columns[1]))
    ts = ts[ts.index.notna()].dropna().sort_index()          # 시계열 분석의 첫걸음: 시간 순 정렬(D3 1-2)
    ts = ts[~ts.index.duplicated(keep="last")]
    if len(ts) < 4:
        raise ValueError("유효한 행이 너무 적습니다(날짜·숫자로 읽힌 행이 4개 미만).")
    freq = pd.infer_freq(ts.index) if len(ts) >= 3 else None
    if freq is None:
        raise ValueError("날짜 간격이 일정하지 않습니다. 빠진 날짜가 없는지 확인하세요(D3 1-4).")
    ts.index = pd.DatetimeIndex(ts.index, freq=freq)
    return ts


# ─────────────────────────────── D4: 시계열 예측(Holt-Winters) ───────────────────────────────
def forecast_timeseries(ts, periods=12, seasonal_periods=12, trend="add", seasonal="mul"):
    """Holt-Winters(삼중 지수평활)로 미래 periods개 시점을 예측합니다.

    반환 dict:
      forecast : 예측값 Series(미래 날짜 인덱스)
      alpha / beta / gamma : 자동으로 찾은 평활 계수(수준/추세/계절성). 해당 성분이 없으면 None
      seasonal / trend     : 실제로 사용한 설정("add"/"mul"/None)
      note     : 설정을 바꿨다면 그 이유
    """
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    ts = ts.astype(float)
    notes = []
    if seasonal is not None and len(ts) < 2 * seasonal_periods:
        # 계절성을 학습하려면 최소 계절 주기의 2배 길이가 필요(D4 4-1)
        notes.append(f"데이터가 {len(ts)}개로 계절 주기({seasonal_periods})의 2배보다 짧아 계절성 없이 예측했습니다.")
        seasonal = None
    if seasonal == "mul" and (ts <= 0).any():
        # 곱셈 계절성은 0 이하 값을 다룰 수 없음
        notes.append("0 이하 값이 있어 곱셈(mul) 대신 덧셈(add) 계절성으로 예측했습니다.")
        seasonal = "add"

    model = ExponentialSmoothing(
        ts,
        trend=trend,
        seasonal=seasonal,
        seasonal_periods=seasonal_periods if seasonal else None,
        initialization_method="estimated",
    ).fit()
    forecast = model.forecast(periods)
    forecast.name = "forecast"

    def _param(name):
        value = model.params.get(name)
        return None if value is None or (isinstance(value, float) and np.isnan(value)) else float(value)

    return {
        "forecast": forecast,
        "alpha": _param("smoothing_level"),
        "beta": _param("smoothing_trend") if trend else None,
        "gamma": _param("smoothing_seasonal") if seasonal else None,
        "trend": trend,
        "seasonal": seasonal,
        "note": " ".join(notes),
    }


def mae(y_true, y_pred):
    """평균절대오차(D4 4-2)."""
    return float(np.mean(np.abs(np.asarray(y_true, dtype=float) - np.asarray(y_pred, dtype=float))))


def mape(y_true, y_pred):
    """평균절대백분율오차(%)(D4 4-2)."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100)


if __name__ == "__main__":
    # 자가 테스트: D4 교안의 검증 결과(132개월 학습 → 12개월 예측, MAE 10.30 / MAPE 2.21%) 재현
    ts, source = load_sample_airpassengers()
    print(f"[데이터] {source}, {len(ts)}개월, 평균 {ts.mean():.1f}")
    train, test = ts.iloc[:-12], ts.iloc[-12:]
    result = forecast_timeseries(train, periods=12)
    print(f"alpha={result['alpha']:.4f} beta={result['beta']:.4f} gamma={result['gamma']:.4f}")
    print(f"MAE={mae(test, result['forecast']):.2f}  MAPE={mape(test, result['forecast']):.2f}%")

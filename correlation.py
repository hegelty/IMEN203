import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr, kendalltau, linregress
from sklearn.preprocessing import PowerTransformer

# 데이터 준비
data = {
    'Company': ['NH투자증권', '미래에셋증권', '상상인증권', '유진증권'],
    'Grade': ['A+', 'A', 'C', 'B'],
    'ROE': [8.45, 7.55, -26.14, -4.72],
    'PBR': [0.59, 0.60, 0.21, 0.25]
}
df = pd.DataFrame(data)

# 등급 숫자 매핑 (Grade는 변환하지 않음)
grade_map = {'S': 7, 'A+': 6, 'A': 5, 'B+': 4, 'B': 3, 'C': 2, 'D': 1}
df['Grade_num'] = df['Grade'].map(grade_map)

# Yeo–Johnson 변환 (ROE, PBR만)
pt = PowerTransformer(method='yeo-johnson', standardize=False)
df[['ROE_yj', 'PBR_yj']] = pt.fit_transform(df[['ROE', 'PBR']])

# 분석 대상 관계 정의
relations = [
    ('Original ROE vs PBR', 'ROE', 'PBR'),
    ('Original Grade vs ROE', 'Grade_num', 'ROE'),
    ('Original Grade vs PBR', 'Grade_num', 'PBR'),
    ('YJ ROE vs YJ PBR', 'ROE_yj', 'PBR_yj'),
    ('Original Grade vs YJ ROE', 'Grade_num', 'ROE_yj'),
    ('Original Grade vs YJ PBR', 'Grade_num', 'PBR_yj'),
]

# stdout으로 수치 출력 및 산점도 그리기
for title, xcol, ycol in relations:
    x = df[xcol]
    y = df[ycol]
    pear_r, pear_p = pearsonr(x, y)
    spea_r, spea_p = spearmanr(x, y)
    kend_r, kend_p = kendalltau(x, y)
    print(f"--- {title} ---")
    print(f"Pearson: r={pear_r:.3f}, p={pear_p:.3f}")
    print(f"Spearman: r={spea_r:.3f}, p={spea_p:.3f}")
    print(f"Kendall: τ={kend_r:.3f}, p={kend_p:.3f}\n")

    # 산점도 + 회귀선
    plt.figure(figsize=(6, 4))
    plt.scatter(x, y, s=60)
    slope, intercept, r_val, _, _ = linregress(x, y)
    xs = np.array([x.min(), x.max()])
    plt.plot(xs, intercept + slope * xs, '--', label=f"R²={r_val ** 2:.3f}")
    plt.title(title)
    plt.xlabel(xcol.replace('_yj', ''))
    plt.ylabel(ycol.replace('_yj', ''))
    plt.legend();
    plt.grid(True)
    plt.savefig(f"{title}.png", dpi=300, bbox_inches='tight')
    plt.show()

# 히트맵: 원본 & Yeo–Johnson
for mat, title, cols in [
    (df[['Grade_num', 'ROE', 'PBR']].corr(), 'Original Correlation Matrix', ['Grade_num', 'ROE', 'PBR']),
    (df[['Grade_num', 'ROE_yj', 'PBR_yj']].corr(), 'Yeo–Johnson Correlation Matrix', ['Grade_num', 'ROE_yj', 'PBR_yj'])
]:
    print(f"--- {title} ---")
    print(mat.to_string(), "\n")
    plt.figure(figsize=(6, 4))
    ax = plt.gca()
    cax = ax.imshow(mat, vmin=-1, vmax=1, cmap='coolwarm')
    ax.set_xticks(range(len(cols)));
    ax.set_xticklabels(cols)
    ax.set_yticks(range(len(cols)));
    ax.set_yticklabels(cols)
    for (i, j), val in np.ndenumerate(mat.values):
        ax.text(j, i, f"{val:.2f}", ha='center', va='center',
                color='white' if abs(val) > 0.5 else 'black')
    plt.title(title)
    plt.colorbar(cax, ax=ax, pad=0.05)
    plt.savefig(f"{title}.png")
    plt.show()

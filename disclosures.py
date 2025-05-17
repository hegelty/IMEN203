import requests
import json
import pandas as pd
from datetime import datetime

API_KEY    = 'YOUR_API_KEY'  # OpenDART API Key
START_DATE = '20240101'   # 조회 시작일
END_DATE   = '20241231'   # 조회 종료일

corp_codes = {
    '상상인증권': '00112059',
    'NH투자증권': '00120182',
    '미래에셋증권': '00111722',
    '유진증권': '00131054',
}

# 정기공시 유형별 기준
reg_types = {
    '사업보고서': {'keyword': '사업보고서', 'period_end': '1231', 'deadline': 90},
    '분기보고서': {'keyword': '분기보고서', 'deadline': 45},  # 분기월 기준 동적
    '반기보고서': {'keyword': '반기보고서', 'period_end': '0630', 'deadline': 45},
}

# 정정·첨부·연장 등 분류 태그
classification_map = {
    '기재정정': '[기재정정]',
    '첨부정정': '[첨부정정]',
    '첨부추가': '[첨부추가]',
    '변경등록': '[변경등록]',
    '연장결정': '[연장결정]',
    '발행조건확정': '[발행조건확정]',
    '정정명령부과': '[정정명령부과]',
    '정정제출요구': '[정정제출요구]',
}

def fetch_all_disclosures(corp_code):
    url = 'https://opendart.fss.or.kr/api/list.json'
    page = 1
    reports = []
    while True:
        params = {
            'crtfc_key': API_KEY,
            'corp_code': corp_code,
            'bgn_de': START_DATE,
            'end_de': END_DATE,
            'last_reprt_at': 'Y',
            'page_no': page,
            'page_count': 100
        }
        resp = requests.get(url, params=params).json()
        reports.extend(resp.get('list', []))
        if page >= int(resp.get('total_page', 1)):
            break
        page += 1
    return reports

def analyze_and_save():
    rows = []
    for comp, code in corp_codes.items():
        # JSON 로드 또는 API 호출
        try:
            with open(f"{comp}_disclosures.json", "r", encoding="utf-8") as f:
                reports = json.load(f)
        except FileNotFoundError:
            reports = fetch_all_disclosures(code)
            with open(f"{comp}_disclosures.json", "w", encoding="utf-8") as f:
                json.dump(reports, f, ensure_ascii=False, indent=2)

        total = len(reports)
        reg = {k: {'cnt': 0, 'on': 0, 'late': []} for k in reg_types}
        classification_counts = {k: 0 for k in classification_map}

        # 주요 보고서 카운트
        g_cnt = sum('기업지배구조보고서' in d['report_nm'] for d in reports)
        s_cnt = sum(any(kw in d['report_nm'] for kw in ['지속가능경영보고서', '통합보고서']) for d in reports)

        for d in reports:
            nm = d['report_nm']
            dt = d.get('rcept_dt', '')
            if len(dt) != 8:
                continue

            # 정기공시 집계 및 적시/지연 체크
            year = dt[:4]
            filed = datetime.strptime(dt, '%Y%m%d')
            for name, info in reg_types.items():
                if info['keyword'] in nm:
                    reg[name]['cnt'] += 1
                    if name == '분기보고서':
                        month = int(dt[4:6])
                        end_mmdd = '0331' if month <= 5 else '0930'
                    else:
                        end_mmdd = info['period_end']
                    end_dt = datetime.strptime(year + end_mmdd, '%Y%m%d')
                    deadline_dt = end_dt + pd.Timedelta(days=info['deadline'])
                    if filed <= deadline_dt:
                        reg[name]['on'] += 1
                    else:
                        delay_days = (filed - deadline_dt).days
                        reg[name]['late'].append({
                            'report_nm': nm,
                            'filed': filed.strftime('%Y-%m-%d'),
                            'deadline': deadline_dt.strftime('%Y-%m-%d'),
                            'delay_days': delay_days
                        })

            # 분류 태그 집계
            for cls, token in classification_map.items():
                if token in nm:
                    classification_counts[cls] += 1

        # 정기공시 지표 계산
        tot_reg = sum(v['cnt'] for v in reg.values())
        tot_on = sum(v['on'] for v in reg.values())
        timely_pct = round(tot_on / tot_reg * 100, 2) if tot_reg else None

        # 총정정건수 및 비율 계산
        total_corrections = sum(classification_counts.values())
        correction_ratio = round(total_corrections / total * 100, 2) if total else None

        # 결과 레코드
        rec = {
            '회사': comp,
            '총공시건수': total,
            '정기공시건수': tot_reg,
            '정기적시제출비율(%)': timely_pct,
            '자율공시건수': sum(1 for d in reports if '자율공시' in d['report_nm']),
            'G-보고서건수': g_cnt,
            'S-보고서건수': s_cnt,
            '총정정건수': total_corrections,
            '정정비율(%)': correction_ratio
        }
        # 정기공시 유형별 건수
        rec.update({f"{k}건수": reg[k]['cnt'] for k in reg})
        # 분류 태그 건수
        rec.update(classification_counts)

        rows.append(rec)

    df = pd.DataFrame(rows)
    df.to_csv('disclosure_metrics_updated.csv', index=False)
    print("▶ 저장됨: disclosure_metrics_updated.csv")
    print(df)

if __name__ == "__main__":
    analyze_and_save()

import os
import math
import time
import threading
import requests
import pandas as pd
import numpy as np
from app.config import Config

STATION_COORDS = {
    "TASH": {"lat": 41.328, "lon": 69.296, "height": 439.7, "name": "Toshkent"},
    "KIT3": {"lat": 39.135, "lon": 66.887, "height": 622.6, "name": "Kitob"},
    "KITG": {"lat": 39.133, "lon": 66.887, "height": 620.6, "name": "Kitob 2"},
    "SAMA": {"lat": 39.654, "lon": 66.959, "height": 702.0, "name": "Samarqand"},
    "BUKH": {"lat": 39.768, "lon": 64.455, "height": 225.0, "name": "Buxoro"},
    "NUKU": {"lat": 42.460, "lon": 59.617, "height": 75.0,  "name": "Nukus"},
    "FERG": {"lat": 40.386, "lon": 71.786, "height": 580.0, "name": "Farg'ona"},
    "ANDI": {"lat": 40.782, "lon": 72.344, "height": 490.0, "name": "Andijon"},
    "NAMA": {"lat": 40.998, "lon": 71.672, "height": 476.0, "name": "Namangan"},
    "JIZZ": {"lat": 40.1158, "lon": 67.8422, "height": 378.0, "name": "Jizzax"},
    "SURX": {"lat": 37.2242, "lon": 67.2783, "height": 302.0, "name": "Termiz"},
    "SIRD": {"lat": 40.4897, "lon": 68.7842, "height": 272.0, "name": "Guliston"},
    "NAVI": {"lat": 40.1039, "lon": 65.3688, "height": 347.0, "name": "Navoiy"},
    "KHOR": {"lat": 41.5500, "lon": 60.6333, "height": 100.0, "name": "Urganch"},
    "QASH": {"lat": 38.8606, "lon": 65.7891, "height": 376.0, "name": "Qarshi"},
    "ZARA": {"lat": 41.5750, "lon": 64.2010, "height": 416.0, "name": "Zarafshon"},
}

ADVECTION_ROUTES = [
    {"from": "TASH", "to": "NAMA", "dir_min": 70, "dir_max": 130, "dist": 210},
    {"from": "TASH", "to": "SIRD", "dir_min": 170, "dir_max": 230, "dist": 90},
    {"from": "SIRD", "to": "JIZZ", "dir_min": 210, "dir_max": 260, "dist": 100},
    {"from": "JIZZ", "to": "SAMA", "dir_min": 220, "dir_max": 270, "dist": 95},
    {"from": "SAMA", "to": "KIT3", "dir_min": 160, "dir_max": 200, "dist": 70},
    {"from": "SAMA", "to": "QASH", "dir_min": 200, "dir_max": 250, "dist": 130},
    {"from": "SAMA", "to": "NAVI", "dir_min": 270, "dir_max": 320, "dist": 140},
    {"from": "NAVI", "to": "BUKH", "dir_min": 230, "dir_max": 280, "dist": 90},
    {"from": "BUKH", "to": "KHOR", "dir_min": 290, "dir_max": 340, "dist": 380},
    {"from": "KHOR", "to": "NUKU", "dir_min": 300, "dir_max": 350, "dist": 140},
    {"from": "FERG", "to": "ANDI", "dir_min": 40,  "dir_max": 90,  "dist": 75},
    {"from": "ANDI", "to": "NAMA", "dir_min": 280, "dir_max": 330, "dist": 70},
    {"from": "QASH", "to": "SURX", "dir_min": 130, "dir_max": 170, "dist": 210},
    {"from": "NAVI", "to": "ZARA", "dir_min": 320, "dir_max": 360, "dist": 180},
    {"from": "BUKH", "to": "ZARA", "dir_min": 340, "dir_max": 30,  "dist": 200},
]

class GNSSService:
    def __init__(self):
        self.df_global = None
        self.live_cache = {}
        self.st_max_dt = {}
        self._load_data()
        self._start_weather_sync()

    def _load_data(self):
        path = Config.GNSS_DATA_PATH
        if os.path.exists(path):
            print(f"[GNSS Service] Parquet yuklanmoqda: {path}")
            self.df_global = pd.read_parquet(path)
            self.st_max_dt = self.df_global.groupby('Station')['datetime'].max().to_dict()
            print(f"[GNSS Service] Yuklandi: {len(self.df_global):,} yozuv")
        else:
            print(f"[GNSS Service XATO] Fayl topilmadi: {path}")
            self.df_global = pd.DataFrame()

    def _start_weather_sync(self):
        t = threading.Thread(target=self._live_weather_loop, daemon=True)
        t.start()

    def _live_weather_loop(self):
        while True:
            try:
                st_list = list(STATION_COORDS.keys())
                lats = ",".join([str(STATION_COORDS[st]["lat"]) for st in st_list])
                lons = ",".join([str(STATION_COORDS[st]["lon"]) for st in st_list])
                url = (f"https://api.open-meteo.com/v1/forecast"
                       f"?latitude={lats}&longitude={lons}"
                       f"&hourly=temperature_2m,relative_humidity_2m,surface_pressure,"
                       f"wind_speed_10m,wind_direction_10m,precipitation_probability,weather_code"
                       f"&timezone=auto&past_days=14&forecast_days=14")
                r = requests.get(url, timeout=25)
                data = r.json()

                if isinstance(data, dict):
                    data = [data]

                new_rows = []
                new_cache = {}
                for i, st in enumerate(st_list):
                    if i >= len(data) or 'hourly' not in data[i]:
                        continue
                    st_data = data[i]['hourly']
                    times = st_data.get('time', [])
                    temps = st_data.get('temperature_2m', [])
                    rhs = st_data.get('relative_humidity_2m', [])
                    pres = st_data.get('surface_pressure', [])
                    wspds = st_data.get('wind_speed_10m', [])
                    wdegs = st_data.get('wind_direction_10m', [])
                    probs = st_data.get('precipitation_probability', [])
                    wcodes = st_data.get('weather_code', [])

                    max_dt = self.st_max_dt.get(st, pd.Timestamp.min)
                    new_cache[st] = {}

                    for j, t_str in enumerate(times):
                        dt_obj = pd.to_datetime(t_str)
                        T = temps[j] if j < len(temps) else None
                        RH = rhs[j] if j < len(rhs) else None
                        P = pres[j] if j < len(pres) else None
                        WS = wspds[j] if j < len(wspds) else None
                        WD = wdegs[j] if j < len(wdegs) else None
                        PR = probs[j] if j < len(probs) else None
                        WC = wcodes[j] if j < len(wcodes) else None

                        h_key = dt_obj.strftime('%Y-%m-%d %H:00')
                        new_cache[st][h_key] = {
                            't': round(T, 1) if T is not None else None,
                            'rh': round(RH, 1) if RH is not None else None,
                            'w_spd': round(WS / 3.6, 1) if WS is not None else None,
                            'w_deg': round(WD, 0) if WD is not None else None,
                            'prob': int(PR) if PR is not None else None,
                            'wcode': int(WC) if WC is not None else None,
                        }

                        if dt_obj > max_dt and T is not None and P is not None and RH is not None:
                            W_spd_ms = round(WS / 3.6, 1) if WS else 0
                            T_k = T + 273.15
                            e = (RH / 100.0) * 6.112 * math.exp((17.67 * T) / (T + 243.5))
                            ZHD = 0.0022768 * P
                            ZWD = 0.0022768 * (1255.0 / T_k + 0.05) * e
                            ZTD = ZHD + ZWD
                            PWV = ZWD * 153.8
                            new_rows.append({
                                'Station': st, 'datetime': dt_obj,
                                'year': dt_obj.year, 'month': dt_obj.month, 'day': dt_obj.day,
                                'Temp': round(T, 1), 'Pressure': round(P, 1), 'RH': round(RH, 1),
                                'ZTD': round(ZTD, 4), 'ZHD': round(ZHD, 4), 'ZWD': round(ZWD, 4),
                                'PWV': round(PWV, 2), 'WindSpd': W_spd_ms, 'WindDeg': WD or 0
                            })

                if new_rows and self.df_global is not None:
                    new_df = pd.DataFrame(new_rows)
                    combined = pd.concat([self.df_global, new_df]).drop_duplicates(subset=['Station', 'datetime'], keep='last')
                    self.df_global = combined.sort_values(by=['Station', 'datetime']).reset_index(drop=True)
                    self.df_global['dPWV'] = self.df_global.groupby('Station')['PWV'].diff().fillna(0).round(2)
                    self.df_global['dP'] = self.df_global.groupby('Station')['Pressure'].diff().fillna(0).round(2)
                    self.df_global['dT'] = self.df_global.groupby('Station')['Temp'].diff().fillna(0).round(2)
                    self.st_max_dt = self.df_global.groupby('Station')['datetime'].max().to_dict()
                    
                    # Yangi hisoblangan datalarni to'g'ridan-to'g'ri Parquet bazasiga yozib saqlab qo'yamiz
                    try:
                        self.df_global.to_parquet(Config.GNSS_DATA_PATH, compression='zstd', index=False)
                        print(f"[GNSS Service] Parquet bazasi yangilandi va saqlandi ({len(self.df_global):,} yozuv).")
                    except Exception as pe:
                        print(f"[GNSS Service Parquet Saqlash Xatosi] {pe}")

                self.live_cache.update(new_cache)
            except Exception as e:
                print(f"[GNSS Weather Sync xatosi] {e}")

            time.sleep(10800) # Har 3 soatda orqa fonda avtomatik yangilab turadi

    @staticmethod
    def calculate_weather(pwv, dpwv, rh, p, dp, dt):
        prob = 0
        if dpwv >= 1.5 and dt <= -1.0 and dp <= -0.5:
            prob += 85
        elif dpwv >= 1.0 and dt <= -0.5:
            prob += 50
        elif dpwv >= 0.5:
            prob += 20
        elif dpwv < -0.5:
            prob -= 20

        if pwv >= 25: prob += 20
        elif pwv >= 20: prob += 10
        elif pwv < 15: prob -= 10

        if rh >= 70: prob += (rh - 60) * 0.5
        elif rh < 50: prob -= 15

        if dp <= -1.0: prob += 15
        elif dp >= 1.0: prob -= 15

        prob = min(100, max(0, round(prob)))
        icon = '☀️'
        label = 'Ochiq havo'
        color = '#FFD700'

        if prob >= 75:
            icon = '⛈️'
            label = 'Jala / Sel xavfi'
            color = '#ff4444'
        elif prob >= 50:
            icon = '🌧️'
            label = "Yomg'ir"
            color = '#4da6ff'
        elif prob >= 25 or rh > 55 or pwv > 18:
            icon = '🌤️'
            label = 'Bulutli / Nam havo'
            color = '#aaaaaa'

        return {"icon": icon, "label": label, "color": color, "prob": prob}

    def get_data(self, st_query='TASH', year=None, month=None, day=None, hour=None):
        if self.df_global is None or self.df_global.empty:
            return {"error": "No data"}

        filtered = self.df_global.copy()
        if year: filtered = filtered[filtered['year'] == year]
        if month: filtered = filtered[filtered['month'] == month]
        if day: filtered = filtered[filtered['day'] == day]
        if hour is not None: filtered = filtered[filtered['datetime'].dt.hour == hour]

        if filtered.empty:
            return {"error": "No data"}

        map_data = []
        current_states = {}

        for st in filtered['Station'].unique():
            st_data = filtered[filtered['Station'] == st].dropna(subset=['PWV']).copy()
            if not st_data.empty and st in STATION_COORDS:
                is_realtime = not day and (not month or month == self.df_global['month'].max()) and (not year or year == self.df_global['year'].max())
                if not is_realtime:
                    latest = st_data.mean(numeric_only=True)
                else:
                    latest = st_data.iloc[-1]

                cache_st = self.live_cache.get(st, {})
                max_prob = 0
                if cache_st:
                    for v_item in cache_st.values():
                        p_val = v_item.get('prob', 0) or 0
                        if p_val > max_prob: max_prob = p_val
                else:
                    for _, row in st_data.iterrows():
                        wx = self.calculate_weather(
                            row.get('PWV', 0) or 0, row.get('dPWV', 0) or 0,
                            row.get('RH', 0) or 0, row.get('Pressure', 0) or 0,
                            row.get('dP', 0) or 0, row.get('dT', 0) or 0
                        )
                        if wx['prob'] > max_prob: max_prob = wx['prob']

                if year and month and day:
                    h_val = hour if hour is not None else pd.Timestamp.now().hour
                    now_key = f"{year}-{month:02d}-{day:02d} {h_val:02d}:00"
                else:
                    now_key = pd.Timestamp.now().strftime('%Y-%m-%d %H:00')

                live = cache_st.get(now_key, {})
                map_t = live.get('t') if live.get('t') is not None else (round(latest.get('Temp', 0), 1) if pd.notna(latest.get('Temp')) else 0)
                map_rh = live.get('rh') if live.get('rh') is not None else (round(latest.get('RH', 0), 1) if pd.notna(latest.get('RH')) else 0)
                map_wsp = live.get('w_spd') if live.get('w_spd') is not None else (round(latest.get('WindSpd', 0), 1) if pd.notna(latest.get('WindSpd')) else 0)
                map_wdg = live.get('w_deg') if live.get('w_deg') is not None else (round(latest.get('WindDeg', 0), 0) if pd.notna(latest.get('WindDeg')) else 0)

                current_states[st] = {
                    "lat": STATION_COORDS[st]["lat"], "lon": STATION_COORDS[st]["lon"],
                    "pwv": round(latest['PWV'], 2),
                    "dpwv": round(latest.get('dPWV', 0), 2),
                    "rh": map_rh, "t": map_t,
                    "dt": round(latest.get('dT', 0), 2),
                    "p": round(latest.get('Pressure', 0), 1),
                    "dp": round(latest.get('dP', 0), 2),
                    "wind_spd": map_wsp,
                    "wind_deg": map_wdg,
                    "max_prob": max_prob
                }

        alerts = []
        seeding_alerts = []

        for route in ADVECTION_ROUTES:
            from_st = route["from"]
            to_st = route["to"]
            if from_st in current_states and to_st in current_states:
                f_data = current_states[from_st]
                f_pwv = f_data["pwv"]
                f_dpwv = f_data["dpwv"]
                f_wdeg = f_data["wind_deg"]
                f_wspd = f_data["wind_spd"]
                f_max_prob = f_data["max_prob"]

                is_dir_match = False
                if route["dir_min"] <= route["dir_max"]:
                    is_dir_match = (route["dir_min"] <= f_wdeg <= route["dir_max"])
                else:
                    is_dir_match = (f_wdeg >= route["dir_min"] or f_wdeg <= route["dir_max"])

                if (f_pwv >= 18.0 or f_dpwv >= 1.0 or f_max_prob >= 60) and f_wspd >= 3.0 and is_dir_match:
                    speed_kmh = f_wspd * 3.6
                    eta_hours = round(route["dist"] / speed_kmh, 1)
                    alerts.append(f"⚠️ {from_st} hududidan nam havo massasi {to_st} tomonga esmoqda! Shamol: {f_wspd} m/s ({f_wdeg}°). Taxminiy yetib borish vaqti: ~{eta_hours} soat (Masofa: {route['dist']} km).")

                if f_pwv >= 15.0 and f_dpwv >= 0.3 and f_data["rh"] >= 45.0 and f_data["dp"] <= -0.1 and f_wspd >= 2.0 and is_dir_match:
                    speed_kmh = f_wspd * 3.6
                    eta_hours = round(route["dist"] / speed_kmh, 1)
                    seeding_alerts.append(f"☁️🚀 [Sun'iy Yomg'ir Qulayligi]: {from_st} hududidagi bulut massasi {to_st} tomonga harakatlanmoqda. Modda sepish samaradorligi yuqori! Yetib borish: ~{eta_hours} soat.")

        for st, data in current_states.items():
            map_data.append({
                "station": st, "lat": data["lat"], "lon": data["lon"],
                "pwv": data["pwv"], "dpwv": data["dpwv"], "rh": data["rh"],
                "t": data["t"], "dt": data["dt"], "p": data["p"], "dp": data["dp"],
                "wind_spd": data["wind_spd"], "wind_deg": data["wind_deg"],
                "max_prob": data["max_prob"]
            })

        plot_df = self.df_global[self.df_global['Station'] == st_query].copy()
        if year: plot_df = plot_df[plot_df['year'] == year]
        if month: plot_df = plot_df[plot_df['month'] == month]
        if day: plot_df = plot_df[plot_df['day'] == day]
        if hour is not None: plot_df = plot_df[plot_df['datetime'].dt.hour == hour]

        if plot_df.empty:
            averages = {k: "--" for k in ['pwv', 'dpwv_max', 'ztd', 'zhd', 'zwd', 't', 'p', 'rh', 'w_spd', 'w_deg']}
        else:
            w_deg_avg = round(plot_df['WindDeg'].dropna().mean(), 1) if 'WindDeg' in plot_df and not plot_df['WindDeg'].dropna().empty else "--"
            averages = {
                "pwv": round(plot_df['PWV'].dropna().mean(), 2) if not plot_df['PWV'].dropna().empty else "--",
                "dpwv_max": round(plot_df['dPWV'].dropna().max(), 2) if not plot_df['dPWV'].dropna().empty else "--",
                "ztd": round(plot_df['ZTD'].dropna().mean(), 4) if not plot_df['ZTD'].dropna().empty else "--",
                "zhd": round(plot_df['ZHD'].dropna().mean(), 4) if not plot_df['ZHD'].dropna().empty else "--",
                "zwd": round(plot_df['ZWD'].dropna().mean(), 4) if not plot_df['ZWD'].dropna().empty else "--",
                "t": round(plot_df['Temp'].dropna().mean(), 2) if not plot_df['Temp'].dropna().empty else "--",
                "p": round(plot_df['Pressure'].dropna().mean(), 2) if not plot_df['Pressure'].dropna().empty else "--",
                "rh": round(plot_df['RH'].dropna().mean(), 2) if not plot_df['RH'].dropna().empty else "--",
                "w_spd": round(plot_df['WindSpd'].dropna().mean(), 2) if 'WindSpd' in plot_df and not plot_df['WindSpd'].dropna().empty else "--",
                "w_deg": w_deg_avg
            }

        # Seeding analysis
        seeding_df = self.df_global[self.df_global['Station'] == st_query].copy()
        timing_list, trajectory_list, convective_list, dry_clouds_list, eval_list = [], [], [], [], []

        if not seeding_df.empty:
            cond_timing = (seeding_df['PWV'] >= 18.0) & (seeding_df['dPWV'] >= 2.0)
            timing_matches = seeding_df[cond_timing].sort_values(by='dPWV', ascending=False).head(8)
            for _, r in timing_matches.iterrows():
                timing_list.append(f"{r['datetime'].strftime('%Y-%m-%d %H:00')} (PWV: {round(r['PWV'],1)}, dPWV: {round(r['dPWV'],1)})")

            cond_conv = (seeding_df['dP'] <= -0.2) & (seeding_df['dT'] <= -0.5)
            conv_matches = seeding_df[cond_conv].sort_values(by=['dT', 'dP']).head(8)
            for _, r in conv_matches.iterrows():
                convective_list.append(f"{r['datetime'].strftime('%Y-%m-%d %H:00')} (dP: {round(r['dP'],1)}, dT: {round(r['dT'],1)})")

            cond_dry = (seeding_df['PWV'] >= 20.0) & (seeding_df['RH'] < 45.0)
            dry_matches = seeding_df[cond_dry].sort_values(by='PWV', ascending=False).head(8)
            for _, r in dry_matches.iterrows():
                dry_clouds_list.append(f"{r['datetime'].strftime('%Y-%m-%d %H:00')} (PWV: {round(r['PWV'],1)}, RH: {round(r['RH'],1)}%)")

            cond_eval = (seeding_df['dPWV'] <= -1.5)
            eval_matches = seeding_df[cond_eval].sort_values(by='dPWV').head(8)
            for _, r in eval_matches.iterrows():
                eval_list.append(f"{r['datetime'].strftime('%Y-%m-%d %H:00')} (Pasayish: {round(r['dPWV'],1)} mm)")

            traj_candidates = seeding_df[(seeding_df['PWV'] >= 15.0) & (seeding_df['WindSpd'] >= 3.0)].sort_values(by='PWV', ascending=False)
            for _, r in traj_candidates.iterrows():
                deg = r['WindDeg']
                spd = r['WindSpd']
                for route in ADVECTION_ROUTES:
                    if route["from"] == st_query:
                        match = False
                        if route["dir_min"] <= route["dir_max"]:
                            match = (route["dir_min"] <= deg <= route["dir_max"])
                        else:
                            match = (deg >= route["dir_min"] or deg <= route["dir_max"])
                        if match:
                            eta = round(route["dist"] / (spd * 3.6), 1)
                            s = f"{r['datetime'].strftime('%Y-%m-%d %H:00')} (➡️ {route['to']} ga ~{eta} soatda)"
                            if s not in trajectory_list:
                                trajectory_list.append(s)
                if len(trajectory_list) >= 8:
                    break

        seeding_analysis = {
            "timing": timing_list, "trajectory": trajectory_list,
            "convective": convective_list, "dry_clouds": dry_clouds_list,
            "evaluation": eval_list
        }

        # Labels & Series
        plot_df = plot_df.sort_values(by='datetime')
        if not day and month:
            plot_df = plot_df.groupby('day').mean(numeric_only=True).reset_index()
            labels = plot_df['day'].astype(int).astype(str).tolist()
        elif not month:
            plot_df = plot_df.groupby('month').mean(numeric_only=True).reset_index()
            labels = plot_df['month'].astype(int).astype(str).tolist()
        else:
            labels = plot_df['datetime'].dt.strftime('%H:%M').tolist()

        def t_l(s, dec):
            return [round(x, dec) if pd.notna(x) else None for x in s]

        return {
            "labels": labels, "station_name": st_query, "averages": averages,
            "alerts": alerts, "seeding_alerts": seeding_alerts, "seeding_analysis": seeding_analysis,
            "pwv": t_l(plot_df.get('PWV', pd.Series(dtype=float)), 2),
            "dpwv": t_l(plot_df.get('dPWV', pd.Series(dtype=float)), 2),
            "ztd": t_l(plot_df.get('ZTD', pd.Series(dtype=float)), 4),
            "zhd": t_l(plot_df.get('ZHD', pd.Series(dtype=float)), 4),
            "zwd": t_l(plot_df.get('ZWD', pd.Series(dtype=float)), 4),
            "t": t_l(plot_df.get('Temp', pd.Series(dtype=float)), 2),
            "p": t_l(plot_df.get('Pressure', pd.Series(dtype=float)), 2),
            "rh": t_l(plot_df.get('RH', pd.Series(dtype=float)), 2),
            "w_spd": t_l(plot_df.get('WindSpd', pd.Series(dtype=float)), 2),
            "w_deg": t_l(plot_df.get('WindDeg', pd.Series(dtype=float)), 0),
            "map": map_data
        }

    def get_hourly(self, st_query='TASH', year=None, month=None, day=None, hour=None):
        if self.df_global is None or self.df_global.empty:
            return {"error": "No data"}

        filtered = self.df_global[self.df_global['Station'] == st_query].copy()
        if year: filtered = filtered[filtered['year'] == year]
        if month: filtered = filtered[filtered['month'] == month]
        if day:
            filtered = filtered[filtered['day'] == day]
        else:
            latest_day = filtered['day'].max()
            filtered = filtered[filtered['day'] == latest_day]

        if filtered.empty:
            return {"error": "No data"}

        filtered = filtered.sort_values('datetime')
        hours = []
        cache_st = self.live_cache.get(st_query, {})

        for _, row in filtered.iterrows():
            pwv = round(row.get('PWV', 0), 2) if pd.notna(row.get('PWV')) else 0
            dpwv = round(row.get('dPWV', 0), 2) if pd.notna(row.get('dPWV')) else 0
            dp = round(row.get('dP', 0), 2) if pd.notna(row.get('dP')) else 0
            is_seeding = bool(pwv >= 15.0 and dpwv >= 0.3 and row.get('RH', 0) >= 45.0 and dp <= -0.1)

            h_key = row['datetime'].strftime('%Y-%m-%d %H:00')
            live = cache_st.get(h_key, {})

            prob = live.get('prob', None)
            temp = live.get('t', round(row.get('Temp', 0), 1) if pd.notna(row.get('Temp')) else 0)
            rh = live.get('rh', round(row.get('RH', 0), 1) if pd.notna(row.get('RH')) else 0)
            w_spd = live.get('w_spd', round(row.get('WindSpd', 0), 1) if pd.notna(row.get('WindSpd')) else 0)
            w_deg = live.get('w_deg', round(row.get('WindDeg', 0), 0) if pd.notna(row.get('WindDeg')) else 0)

            if prob is None:
                wx = self.calculate_weather(pwv, dpwv, rh, round(row.get('Pressure', 0), 1), dp, round(row.get('dT', 0), 2))
                prob = wx['prob']

            hours.append({
                "time": row['datetime'].strftime('%H:%M'),
                "date": row['datetime'].strftime('%Y-%m-%d'),
                "t": temp, "rh": rh,
                "p": round(row.get('Pressure', 0), 1) if pd.notna(row.get('Pressure')) else 0,
                "pwv": pwv, "dpwv": dpwv,
                "w_spd": w_spd, "w_deg": w_deg,
                "prob": prob, "is_seeding": is_seeding
            })

        station_info = STATION_COORDS.get(st_query, {})
        return {
            "station": st_query,
            "lat": station_info.get('lat', 0),
            "lon": station_info.get('lon', 0),
            "hours": hours
        }

# Global singleton service
gnss_service = GNSSService()

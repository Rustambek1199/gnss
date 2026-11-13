import os
import io
import base64
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from app.config import Config

class ChangService:
    def __init__(self):
        self.df = None
        self.ml_model = None
        self.ml_features = ['wind_speed', 'wind_dir', 'swvl1', 'PWV', 'ZTD']
        self._load_data()
        self._train_model()

    def _load_data(self):
        path = Config.CHANG_DATA_PATH
        if os.path.exists(path):
            print(f"[Chang Service] Parquet yuklanmoqda: {path}")
            self.df = pd.read_parquet(path)
            print(f"[Chang Service] Yuklandi: {len(self.df)} qator")
        else:
            print(f"[Chang Service XATO] Fayl topilmadi: {path}")
            self.df = pd.DataFrame()

    def _train_model(self):
        if self.df is None or self.df.empty:
            return
        try:
            X = self.df[self.ml_features]
            y = self.df['dust_storm']
            X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
            self.ml_model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
            self.ml_model.fit(X_train, y_train)
            print("[Chang Service] Random Forest modeli o'qitildi.")
        except Exception as e:
            print(f"[Chang Service ML xatosi]: {e}")

    def get_data(self, region='Navoiy', year='', month='', day='', start_date=None, end_date=None):
        if self.df is None or self.df.empty:
            return {"error": "No data"}

        if 'region' in self.df.columns:
            df_filtered = self.df[self.df['region'] == region].copy()
        else:
            df_filtered = self.df.copy()

        if len(df_filtered) > 0:
            min_date = df_filtered.index.min().strftime('%Y-%m-%d')
            max_date = df_filtered.index.max().strftime('%Y-%m-%d')
        else:
            min_date = '2021-01-01'
            max_date = '2026-12-31'

        if year:
            df_filtered = df_filtered[df_filtered.index.year == int(year)]
        if month:
            df_filtered = df_filtered[df_filtered.index.month == int(month)]
        if day:
            df_filtered = df_filtered[df_filtered.index.day == int(day)]
        if start_date and end_date:
            df_filtered = df_filtered.loc[start_date:end_date]

        if len(df_filtered) == 0:
            if 'region' in self.df.columns:
                df_filtered = self.df[self.df['region'] == region].iloc[-30:].copy()
            else:
                df_filtered = self.df.iloc[-30:].copy()

        latest = df_filtered.iloc[-1]
        dates = df_filtered.index.strftime('%Y-%m-%d').tolist()
        ndvi = df_filtered['NDVI'].tolist()
        swvl1 = df_filtered['swvl1'].tolist()
        risk_index = df_filtered['Risk_Index'].tolist()

        # Map points
        np.random.seed(42)
        map_data = []
        navoiy_points = [
            {'lat': 40.10, 'lon': 65.37, 'name': 'Navoiy shahri atrofi', 'base_risk': 55},
            {'lat': 40.50, 'lon': 65.60, 'name': 'Qiziltepa tumani', 'base_risk': 60},
            {'lat': 40.78, 'lon': 65.03, 'name': 'Navbahor tumani', 'base_risk': 65},
            {'lat': 41.55, 'lon': 64.17, 'name': 'Zarafshon shahri', 'base_risk': 70},
            {'lat': 42.00, 'lon': 64.60, 'name': "Tomdi tumani (cho'l)", 'base_risk': 90},
            {'lat': 41.10, 'lon': 63.85, 'name': 'Uchquduq tumani', 'base_risk': 92},
            {'lat': 42.50, 'lon': 63.50, 'name': "Qizilqum cho'li shimoli", 'base_risk': 95},
            {'lat': 41.80, 'lon': 62.80, 'name': "Qizilqum cho'li g'arbi", 'base_risk': 93},
            {'lat': 40.35, 'lon': 65.80, 'name': 'Konimex tumani', 'base_risk': 58},
            {'lat': 41.20, 'lon': 64.80, 'name': 'Nurota tumani', 'base_risk': 72},
            {'lat': 40.60, 'lon': 64.50, 'name': 'Xatirchi tumani', 'base_risk': 68},
            {'lat': 42.80, 'lon': 64.00, 'name': "Shimoliy cho'l hududlari", 'base_risk': 88},
            {'lat': 40.22, 'lon': 65.10, 'name': 'Navoiy yaylovlari', 'base_risk': 62},
            {'lat': 41.00, 'lon': 65.50, 'name': 'Karmana tumani', 'base_risk': 55},
            {'lat': 42.20, 'lon': 63.00, 'name': "Uchquduq cho'li", 'base_risk': 94},
            {'lat': 41.50, 'lon': 63.20, 'name': "Mingbuloq cho'li", 'base_risk': 91},
            {'lat': 42.60, 'lon': 62.50, 'name': "Qizilqum markazi", 'base_risk': 96},
        ]
        buxoro_points = [
            {'lat': 39.77, 'lon': 64.42, 'name': 'Buxoro shahri atrofi', 'base_risk': 45},
            {'lat': 39.50, 'lon': 64.20, 'name': "Qorako'l tumani", 'base_risk': 70},
            {'lat': 40.10, 'lon': 64.00, 'name': 'Jondor tumani', 'base_risk': 55},
            {'lat': 40.30, 'lon': 63.60, 'name': "G'ijduvon tumani", 'base_risk': 50},
            {'lat': 39.90, 'lon': 63.50, 'name': 'Romitan tumani', 'base_risk': 58},
            {'lat': 39.30, 'lon': 63.90, 'name': "Olot tumani (cho'l)", 'base_risk': 82},
            {'lat': 40.50, 'lon': 63.20, 'name': 'Shofirkon tumani', 'base_risk': 48},
            {'lat': 39.60, 'lon': 64.80, 'name': 'Kogon tumani', 'base_risk': 42},
            {'lat': 40.00, 'lon': 64.60, 'name': 'Vobkent tumani', 'base_risk': 40},
            {'lat': 39.20, 'lon': 64.60, 'name': 'Janubiy Buxoro yaylovlari', 'base_risk': 75},
            {'lat': 39.85, 'lon': 63.10, 'name': "G'arbiy cho'l hududlari", 'base_risk': 80},
            {'lat': 39.40, 'lon': 63.50, 'name': "Qorako'l cho'li", 'base_risk': 85},
            {'lat': 39.70, 'lon': 63.80, 'name': 'Buxoro yaylovlari', 'base_risk': 65},
        ]
        all_points = navoiy_points + buxoro_points
        for pt in all_points:
            noise = np.random.uniform(-5, 5)
            risk = float(np.clip(pt['base_risk'] + noise, 10, 98))
            map_data.append({'lat': pt['lat'], 'lon': pt['lon'], 'risk': risk, 'name': pt['name']})

        # Wind analysis
        df_filtered = df_filtered.copy()
        df_filtered['is_dangerous'] = (df_filtered['wind_speed'] > 7.0) & (df_filtered['swvl1'] < 0.15)
        df_filtered['month'] = df_filtered.index.month
        dangerous_months = df_filtered.groupby('month')['is_dangerous'].sum().reindex(range(1, 13), fill_value=0).reset_index()
        dangerous_months.columns = ['month', 'is_dangerous']

        bin_names = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        df_filtered['sector_idx'] = np.round(df_filtered['wind_dir'] / 22.5).astype(int) % 16
        wind_rose_grouped = df_filtered.groupby('sector_idx').agg(
            frequency=('wind_speed', 'count'),
            mean_speed=('wind_speed', 'mean')
        ).reindex(range(16), fill_value=0).reset_index()
        wind_rose_grouped['mean_speed'] = wind_rose_grouped['mean_speed'].fillna(0)
        wind_rose_grouped['direction'] = bin_names

        # Feature importances
        if self.ml_model:
            importances = dict(zip(self.ml_features, self.ml_model.feature_importances_.tolist()))
        else:
            importances = {'wind_speed': 0.4, 'swvl1': 0.25, 'PWV': 0.15, 'wind_dir': 0.1, 'ZTD': 0.1}

        # Latest prediction
        features_latest = pd.DataFrame([[latest[f] for f in self.ml_features]], columns=self.ml_features)
        if self.ml_model:
            pred = int(self.ml_model.predict(features_latest)[0])
            prob = float(self.ml_model.predict_proba(features_latest)[0][1])
        else:
            pred = 0
            prob = 0.25

        return {
            'metrics': {
                'wind_speed': f"{latest['wind_speed']:.1f}",
                'soil_moisture': f"{latest['swvl1']*100:.1f}",
                'ndvi': f"{latest['NDVI']:.2f}",
                'risk_index': f"{latest['Risk_Index']:.0f}"
            },
            'timeseries': {'dates': dates, 'ndvi': ndvi, 'swvl1': swvl1, 'risk_index': risk_index},
            'map_data': map_data,
            'dangerous_months': {'months': dangerous_months['month'].tolist(), 'counts': dangerous_months['is_dangerous'].tolist()},
            'wind_rose': {'directions': wind_rose_grouped['direction'].tolist(), 'frequencies': wind_rose_grouped['frequency'].tolist(), 'mean_speeds': wind_rose_grouped['mean_speed'].round(1).tolist()},
            'feature_importance': importances,
            'prediction': pred,
            'probability': prob,
            'date_bounds': {'min': min_date, 'max': max_date}
        }

    def predict(self, data):
        if not self.ml_model:
            return {'prediction': 0, 'probability': 0.1}
        features = pd.DataFrame([[
            float(data.get('wind_speed', 7.8)),
            float(data.get('wind_dir', 315)),
            float(data.get('swvl1', 0.11)),
            float(data.get('pwv', 9.5)),
            float(data.get('ztd', 2.35))
        ]], columns=self.ml_features)
        pred = int(self.ml_model.predict(features)[0])
        prob = float(self.ml_model.predict_proba(features)[0][1])
        return {'prediction': pred, 'probability': prob}

    def simulate(self, barriers=None, barrier_height=20):
        if barriers is None:
            barriers = [50, 150, 250]

        is_default = (barriers == [50, 150, 250] and barrier_height == 20)
        cache_path = Config.SIM_IMAGE_PATH

        # Return precomputed image immediately
        if is_default and os.path.exists(cache_path):
            with open(cache_path, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{img_b64}"

        # Vectorized fast simulation (~0.05s)
        Nx, Ny = 300, 100
        dx, dy = 1.0, 1.0
        dt = 0.05
        steps = 800
        U0, D, Ws = 5.0, 0.2, 0.1

        U = np.ones((Ny, Nx)) * U0
        V = np.zeros((Ny, Nx))

        for bx in barriers:
            if bx < Nx:
                U[:barrier_height, bx:min(bx+3, Nx)] = U0 * 0.1
                for i in range(1, 80):
                    if bx + 3 + i < Nx:
                        recovery_factor = 1.0 - 0.8 * np.exp(-i / 20.0)
                        U[:barrier_height, bx+3+i] = U0 * recovery_factor
                        if i < 15 and barrier_height + 10 < Ny:
                            V[barrier_height:barrier_height+10, bx+3+i] = U0 * 0.2 * np.exp(-i/5.0)

        C = np.zeros((Ny, Nx))
        C[:, 0] = 100.0

        for t in range(steps):
            adv_x = U[1:-1, 1:-1] * (C[1:-1, 1:-1] - C[1:-1, :-2]) / dx
            adv_y = (V[1:-1, 1:-1] - Ws) * (C[1:-1, 1:-1] - C[:-2, 1:-1]) / dy
            diff_x = D * (C[1:-1, 2:] - 2*C[1:-1, 1:-1] + C[1:-1, :-2]) / (dx**2)
            diff_y = D * (C[2:, 1:-1] - 2*C[1:-1, 1:-1] + C[:-2, 1:-1]) / (dy**2)
            C[1:-1, 1:-1] += dt * (-adv_x - adv_y + diff_x + diff_y)
            C[:, 0] = 100.0

        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(11, 4.5), facecolor='#0b1120', dpi=120)
        c_plot = ax.contourf(C, levels=50, cmap='YlOrBr', alpha=0.9)
        cbar = plt.colorbar(c_plot, ax=ax)
        cbar.set_label("Qum konsentratsiyasi (ppm)", color='#e2e8f0', fontsize=11, fontweight='bold')
        cbar.ax.yaxis.set_tick_params(color='#e2e8f0')
        cbar.outline.set_edgecolor('#334155')
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#e2e8f0')

        for bx in barriers:
            ax.plot([bx, bx], [0, barrier_height], color='#10b981', linewidth=4.5, label="Yashil to'siq (Daraxtzor)" if bx==barriers[0] else "")

        ax.set_title("Yashil To'siqlar Bo'ylab Qum Va Chang Difuziya-Adveksiya Modeli", color='#f8fafc', fontsize=12, fontweight='bold', pad=12)
        ax.set_xlabel("Masofa (metr)", color='#94a3b8', fontsize=10)
        ax.set_ylabel("Balandlik (metr)", color='#94a3b8', fontsize=10)
        ax.tick_params(colors='#94a3b8')
        for spine in ax.spines.values():
            spine.set_edgecolor('#334155')

        ax.legend(facecolor='#0f172a', edgecolor='#3b82f6', loc='upper right', fontsize=10)

        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', facecolor='#0b1120')
        img.seek(0)
        img_bytes = img.getvalue()
        img_b64 = base64.b64encode(img_bytes).decode()
        plt.close()

        if is_default:
            try:
                with open(cache_path, 'wb') as f:
                    f.write(img_bytes)
            except Exception:
                pass

        return f"data:image/png;base64,{img_b64}"

    def calculate_barrier_impact(self, barriers=None, barrier_height=20):
        if barriers is None:
            barriers = [50, 150, 250]

        Nx, Ny = 300, 100
        dx, dy = 1.0, 1.0
        dt = 0.05
        steps = 800
        U0, D, Ws = 5.0, 0.2, 0.1

        def run_sim(barrier_list):
            U = np.ones((Ny, Nx)) * U0
            V = np.zeros((Ny, Nx))
            for bx in barrier_list:
                if bx < Nx:
                    U[:barrier_height, bx:min(bx+3, Nx)] = U0 * 0.1
                    for i in range(1, 80):
                        if bx + 3 + i < Nx:
                            recovery_factor = 1.0 - 0.8 * np.exp(-i / 20.0)
                            U[:barrier_height, bx+3+i] = U0 * recovery_factor
                            if i < 15 and barrier_height + 10 < Ny:
                                V[barrier_height:barrier_height+10, bx+3+i] = U0 * 0.2 * np.exp(-i/5.0)

            C = np.zeros((Ny, Nx))
            C[:, 0] = 100.0

            for t in range(steps):
                adv_x = U[1:-1, 1:-1] * (C[1:-1, 1:-1] - C[1:-1, :-2]) / dx
                adv_y = (V[1:-1, 1:-1] - Ws) * (C[1:-1, 1:-1] - C[:-2, 1:-1]) / dy
                diff_x = D * (C[1:-1, 2:] - 2*C[1:-1, 1:-1] + C[1:-1, :-2]) / (dx**2)
                diff_y = D * (C[2:, 1:-1] - 2*C[1:-1, 1:-1] + C[:-2, 1:-1]) / (dy**2)
                C[1:-1, 1:-1] += dt * (-adv_x - adv_y + diff_x + diff_y)
                C[:, 0] = 100.0
            return C

        C_no = run_sim([])
        C_yes = run_sim(barriers)
        protected_zone = slice(50, Nx)
        d_no = float(np.sum(C_no[:, protected_zone]))
        d_yes = float(np.sum(C_yes[:, protected_zone]))

        reduction = ((d_no - d_yes) / d_no) * 100 if d_no > 0 else 0.0
        return {
            'dust_reduction_percentage': float(reduction),
            'total_dust_without_barriers': float(d_no),
            'total_dust_with_barriers': float(d_yes)
        }

# Global singleton service
chang_service = ChangService()

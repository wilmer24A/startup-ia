content = '''"""
Dashboard de analytics completo para TechHelper AI.
Combina funnel, retención, eventos y métricas en un solo lugar.
"""
from src.analytics.tracker import tracker
from src.analytics.funnel import AnalizadorFunnel
from src.analytics.retencion import AnalizadorRetencion
from src.billing.metricas import MetricasBilling
from datetime import datetime


class DashboardAnalytics:
    """
    Dashboard completo de analytics para el operador.
    """

    def __init__(self):
        self.funnel = AnalizadorFunnel()
        self.retencion = AnalizadorRetencion()
        self.billing = MetricasBilling()

    def generar(self) -> dict:
        """Genera el dashboard completo."""
        return {
            "timestamp": datetime.now().isoformat(),
            "resumen": self._resumen_ejecutivo(),
            "usuarios": self._metricas_usuarios(),
            "engagement": self._metricas_engagement(),
            "conversion": self._metricas_conversion(),
            "revenue": self._metricas_revenue(),
        }

    def _resumen_ejecutivo(self) -> dict:
        """Resumen ejecutivo del estado del producto."""
        billing = self.billing.generar_dashboard()
        retencion = self.retencion.calcular_retencion_simple()

        return {
            "total_usuarios": billing["usuarios"]["total"],
            "mrr": billing["revenue"]["mrr_formateado"],
            "tasa_pago": billing["conversion"]["tasa_pago"],
            "retencion_semanal": retencion["tasa_retencion"],
        }

    def _metricas_usuarios(self) -> dict:
        """Métricas de usuarios por plan."""
        billing = self.billing.generar_dashboard()
        return billing["usuarios"]

    def _metricas_engagement(self) -> dict:
        """Métricas de engagement — cómo usan el producto."""
        categorias = self.funnel.categorias_mas_usadas()
        actividad = self.retencion.usuarios_activos_por_semana(semanas=4)

        return {
            "categorias_chat": categorias,
            "actividad_semanal": actividad,
            "usuarios_una_vez": self.retencion.usuarios_nunca_regresaron(),
        }

    def _metricas_conversion(self) -> dict:
        """Métricas del funnel de conversión."""
        funnel = self.funnel.calcular_funnel()
        return {
            "pasos": funnel,
            "paso_mayor_abandono": max(
                funnel, key=lambda x: x["abandono_desde_anterior"]
            )["paso"] if funnel else "N/A"
        }

    def _metricas_revenue(self) -> dict:
        """Métricas de revenue."""
        billing = self.billing.generar_dashboard()
        return billing["revenue"]

    def mostrar(self) -> None:
        """Muestra el dashboard en formato legible."""
        dashboard = self.generar()

        print("=" * 60)
        print("DASHBOARD DE ANALYTICS — TECHHELPER AI")
        print(f"Generado: {dashboard[\'timestamp\'][:19]}")
        print("=" * 60)

        resumen = dashboard["resumen"]
        print("\\n📊 RESUMEN EJECUTIVO")
        print(f"  Usuarios totales:    {resumen[\'total_usuarios\']}")
        print(f"  MRR:                 {resumen[\'mrr\']}")
        print(f"  Tasa de pago:        {resumen[\'tasa_pago\']}")
        print(f"  Retención semanal:   {resumen[\'retencion_semanal\']}")

        print("\\n💬 ENGAGEMENT")
        engagement = dashboard["engagement"]
        print(f"  Categorías más usadas:")
        for cat, count in engagement["categorias_chat"].items():
            print(f"    {cat}: {count}")
        print(f"  Usuarios solo una vez: {engagement[\'usuarios_una_vez\']}")

        print("\\n📈 CONVERSIÓN")
        conversion = dashboard["conversion"]
        print(f"  Mayor abandono en: {conversion[\'paso_mayor_abandono\']}")

        print("\\n💰 REVENUE")
        revenue = dashboard["revenue"]
        print(f"  MRR: {revenue[\'mrr_formateado\']}")
        print(f"  ARR: {revenue[\'arr_formateado\']}")
        print("=" * 60)


if __name__ == "__main__":
    dashboard = DashboardAnalytics()
    dashboard.mostrar()
'''

with open('src/analytics/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Dashboard de analytics creado correctamente")
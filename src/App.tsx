import { useState, useEffect } from 'react';
import { Download, Copy, Check, ChevronDown, ChevronUp, Flame, TrendingUp, TrendingDown, AlertCircle, Info, FileCode, Package } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<'preview' | 'code' | 'requirements' | 'packages'>('preview');
  const [copied, setCopied] = useState<string | null>(null);
  const [showLegend, setShowLegend] = useState(true);
  const [pythonCode, setPythonCode] = useState('');
  const [requirementsCode, setRequirementsCode] = useState('');

  useEffect(() => {
    fetch('/app.py')
      .then(res => res.text())
      .then(text => setPythonCode(text))
      .catch(() => setPythonCode('# Error loading file'));
    
    fetch('/requirements.txt')
      .then(res => res.text())
      .then(text => setRequirementsCode(text))
      .catch(() => setRequirementsCode('# Error loading file'));
  }, []);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const downloadFile = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      {/* Header */}
      <header className="border-b border-gray-700 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-600 rounded-xl flex items-center justify-center shadow-lg shadow-orange-500/20">
                <Flame className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-orange-400 to-red-500 bg-clip-text text-transparent">
                  Control Maestro v9.0
                </h1>
                <p className="text-sm text-gray-400">ARIMA + GARCH + Análisis Técnico</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => downloadFile(pythonCode, 'app.py')}
                className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg font-medium transition-colors"
              >
                <Download className="w-4 h-4" />
                app.py
              </button>
              <button
                onClick={() => downloadFile(requirementsCode, 'requirements.txt')}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition-colors"
              >
                <Download className="w-4 h-4" />
                requirements.txt
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="border-b border-gray-700 bg-gray-800/50 overflow-x-auto">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-1">
            {[
              { id: 'preview', label: 'Vista Previa', icon: TrendingUp },
              { id: 'code', label: 'Código Python', icon: FileCode },
              { id: 'requirements', label: 'Requirements.txt', icon: Package },
              { id: 'packages', label: 'Info Paquetes', icon: Info },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`flex items-center gap-2 px-4 py-3 font-medium transition-colors border-b-2 whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-orange-500 text-orange-400 bg-gray-800/50'
                    : 'border-transparent text-gray-400 hover:text-white hover:bg-gray-700/50'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'preview' && (
          <div className="space-y-6">
            {/* Legend Section */}
            <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
              <button
                onClick={() => setShowLegend(!showLegend)}
                className="w-full flex items-center justify-between p-4 hover:bg-gray-700/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-600/20 rounded-lg flex items-center justify-center">
                    <Info className="w-5 h-5 text-blue-400" />
                  </div>
                  <h2 className="text-lg font-semibold">📖 GUÍA RÁPIDA: ¿Qué significa todo esto?</h2>
                </div>
                {showLegend ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              </button>
              
              {showLegend && (
                <div className="p-6 pt-0 space-y-6">
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {[
                      { icon: '📊', title: 'POC (Línea Roja)', desc: 'Precio donde hubo MÁS volumen. Actúa como soporte/resistencia fuerte.' },
                      { icon: '📈', title: 'VWAP (Línea Cyan)', desc: 'Precio promedio del día. Arriba = tendencia alcista. Abajo = bajista.' },
                      { icon: '💠', title: 'Diamante Azul', desc: 'Alto volumen + baja volatilidad. Posible cambio de dirección próximo.' },
                      { icon: '🔮', title: 'ARIMA', desc: 'Predice precio futuro. Verde ↑ = sube. Rojo ↓ = baja.' },
                      { icon: '📉', title: 'GARCH', desc: 'Mide volatilidad futura. Alta = más riesgo, reduce posición.' },
                      { icon: '🔥', title: 'FUEGO MAESTRO', desc: 'Cuando 5m, 15m y 1H coinciden. ¡Señal más fuerte!' },
                    ].map((item, i) => (
                      <div key={i} className="bg-gray-700/50 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-2xl">{item.icon}</span>
                          <h3 className="font-semibold text-white">{item.title}</h3>
                        </div>
                        <p className="text-sm text-gray-300">{item.desc}</p>
                      </div>
                    ))}
                  </div>
                  
                  <div className="bg-gradient-to-r from-orange-900/30 to-red-900/30 rounded-lg p-4 border border-orange-700/30">
                    <h3 className="font-bold text-orange-400 mb-3">⚡ REGLAS SIMPLES PARA OPERAR:</h3>
                    <ul className="space-y-2 text-sm">
                      <li className="flex items-start gap-2">
                        <span className="text-orange-400">1.</span>
                        <span><strong>🔥 FUEGO MAESTRO</strong> → Considera entrar en esa dirección</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-orange-400">2.</span>
                        <span><strong>📈 ARIMA sube + GARCH bajo</strong> → Buena oportunidad de COMPRA</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-orange-400">3.</span>
                        <span><strong>📉 ARIMA baja + GARCH bajo</strong> → Buena oportunidad de VENTA</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-orange-400">4.</span>
                        <span><strong>⚠️ GARCH MUY ALTO</strong> → ¡CUIDADO! Reduce tu riesgo</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-orange-400">5.</span>
                        <span><strong>⚖️ Timeframes no coinciden</strong> → NO OPERES, espera</span>
                      </li>
                    </ul>
                  </div>
                </div>
              )}
            </div>

            {/* Preview Cards */}
            {['🥇 Oro (Gold)', '💴 Yen (USD/JPY)', '₿ Bitcoin (BTC/USD)'].map((asset, idx) => (
              <div key={idx} className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
                <div className="p-4 border-b border-gray-700">
                  <h3 className="text-xl font-bold">{asset}</h3>
                </div>
                
                <div className="p-4 grid md:grid-cols-2 gap-4">
                  <div className="bg-gradient-to-br from-purple-900/30 to-blue-900/30 rounded-lg p-4 border border-purple-700/30">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl">🔮</span>
                      <span className="text-sm text-gray-400">ARIMA - Predicción</span>
                    </div>
                    <div className="text-2xl font-bold text-white">
                      {idx === 0 ? '$2,347.50' : idx === 1 ? '¥157.32' : '$67,890.00'}
                    </div>
                    <div className={`flex items-center gap-1 mt-1 ${idx === 1 ? 'text-red-400' : 'text-green-400'}`}>
                      {idx === 1 ? <TrendingDown className="w-4 h-4" /> : <TrendingUp className="w-4 h-4" />}
                      <span className="text-sm font-medium">
                        {idx === 0 ? '+0.45% SUBE 📈' : idx === 1 ? '-0.23% BAJA 📉' : '+1.25% SUBE 📈'}
                      </span>
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-br from-orange-900/30 to-red-900/30 rounded-lg p-4 border border-orange-700/30">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl">📉</span>
                      <span className="text-sm text-gray-400">GARCH - Volatilidad</span>
                    </div>
                    <div className="text-2xl font-bold text-white">
                      {idx === 0 ? '12.5%' : idx === 1 ? '8.2%' : '28.7%'}
                    </div>
                    <div className={`text-sm font-medium mt-1 ${
                      idx === 2 ? 'text-red-400' : idx === 1 ? 'text-blue-400' : 'text-green-400'
                    }`}>
                      {idx === 0 ? '🟢 NORMAL' : idx === 1 ? '🔵 BAJA' : '🔴 MUY ALTA'}
                    </div>
                  </div>
                </div>

                <div className="p-4 grid grid-cols-3 gap-4">
                  {['5m', '15m', '1h'].map((tf, tfIdx) => (
                    <div key={tf} className="bg-gray-900 rounded-lg p-4 text-center">
                      <div className="text-sm text-gray-400 mb-2">TF: {tf}</div>
                      <div className="h-24 bg-gray-800 rounded flex items-center justify-center mb-2 border border-gray-700">
                        <div className="text-gray-500 text-sm">[Gráfico {tf}]</div>
                      </div>
                      <div className={`inline-block px-3 py-1 rounded-full text-sm font-bold ${
                        (idx === 0 || idx === 2) 
                          ? 'bg-green-600/30 text-green-400' 
                          : tfIdx === 2 
                            ? 'bg-green-600/30 text-green-400' 
                            : 'bg-red-600/30 text-red-400'
                      }`}>
                        {(idx === 0 || idx === 2) ? 'COMPRA' : tfIdx === 2 ? 'COMPRA' : 'VENTA'}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="p-4 border-t border-gray-700">
                  <div className="flex items-center gap-3">
                    {idx === 0 || idx === 2 ? (
                      <div className="flex-1 bg-gradient-to-r from-orange-600/30 to-red-600/30 border border-orange-500/50 rounded-lg p-3 text-center">
                        <span className="text-xl">🔥🔥🔥</span>
                        <span className="ml-2 font-bold text-orange-400">¡FUEGO MAESTRO DETECTADO! ALINEACIÓN TOTAL DE COMPRA</span>
                        <span className="ml-2 text-xl">🔥🔥🔥</span>
                      </div>
                    ) : (
                      <div className="flex-1 bg-blue-600/20 border border-blue-500/50 rounded-lg p-3 text-center">
                        <AlertCircle className="w-5 h-5 inline mr-2 text-blue-400" />
                        <span className="font-medium text-blue-400">⚖️ MERCADO MIXTO: Los tiempos no coinciden. Espera mejor alineación.</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'code' && (
          <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-gray-700 flex-wrap gap-2">
              <h2 className="font-semibold flex items-center gap-2">
                <FileCode className="w-5 h-5 text-green-400" />
                app.py - Código Python Mejorado
              </h2>
              <div className="flex gap-2">
                <button
                  onClick={() => copyToClipboard(pythonCode, 'code')}
                  className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
                >
                  {copied === 'code' ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                  {copied === 'code' ? 'Copiado!' : 'Copiar'}
                </button>
                <button
                  onClick={() => downloadFile(pythonCode, 'app.py')}
                  className="flex items-center gap-2 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-sm transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Descargar
                </button>
              </div>
            </div>
            <pre className="p-4 overflow-x-auto text-sm bg-gray-900 max-h-[600px] overflow-y-auto">
              <code className="text-gray-300">{pythonCode || 'Cargando...'}</code>
            </pre>
          </div>
        )}

        {activeTab === 'requirements' && (
          <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-gray-700 flex-wrap gap-2">
              <h2 className="font-semibold flex items-center gap-2">
                <Package className="w-5 h-5 text-blue-400" />
                requirements.txt
              </h2>
              <div className="flex gap-2">
                <button
                  onClick={() => copyToClipboard(requirementsCode, 'req')}
                  className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
                >
                  {copied === 'req' ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                  {copied === 'req' ? 'Copiado!' : 'Copiar'}
                </button>
                <button
                  onClick={() => downloadFile(requirementsCode, 'requirements.txt')}
                  className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Descargar
                </button>
              </div>
            </div>
            <pre className="p-6 bg-gray-900 text-lg">
              <code className="text-gray-300">{requirementsCode || 'Cargando...'}</code>
            </pre>
          </div>
        )}

        {activeTab === 'packages' && (
          <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <h2 className="font-semibold flex items-center gap-2">
                <Info className="w-5 h-5 text-purple-400" />
                Información de Paquetes
              </h2>
            </div>
            <div className="p-6">
              <div className="bg-gray-900 rounded-lg p-6 space-y-6">
                <h3 className="text-xl font-bold text-white">📦 Dependencias del Proyecto</h3>
                
                <div>
                  <h4 className="text-lg font-semibold text-blue-400 mb-2">Instalación Rápida:</h4>
                  <div className="bg-gray-800 rounded p-3 font-mono text-sm border border-gray-700">
                    pip install -r requirements.txt
                  </div>
                </div>

                <div>
                  <h4 className="text-lg font-semibold text-green-400 mb-3">Descripción de cada paquete:</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-700">
                          <th className="text-left py-2 px-4 text-gray-400">Paquete</th>
                          <th className="text-left py-2 px-4 text-gray-400">Versión</th>
                          <th className="text-left py-2 px-4 text-gray-400">¿Para qué sirve?</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-700">
                        <tr><td className="py-2 px-4 font-mono text-blue-400">streamlit</td><td className="py-2 px-4">1.31.0</td><td className="py-2 px-4">Framework para crear la interfaz web interactiva</td></tr>
                        <tr><td className="py-2 px-4 font-mono text-blue-400">yfinance</td><td className="py-2 px-4">0.2.36</td><td className="py-2 px-4">Descarga datos de precios en tiempo real (Yahoo Finance)</td></tr>
                        <tr><td className="py-2 px-4 font-mono text-blue-400">pandas</td><td className="py-2 px-4">2.2.0</td><td className="py-2 px-4">Manejo y análisis de datos en tablas</td></tr>
                        <tr><td className="py-2 px-4 font-mono text-blue-400">numpy</td><td className="py-2 px-4">1.26.3</td><td className="py-2 px-4">Cálculos matemáticos y estadísticos</td></tr>
                        <tr><td className="py-2 px-4 font-mono text-blue-400">matplotlib</td><td className="py-2 px-4">3.8.2</td><td className="py-2 px-4">Creación de gráficos y visualizaciones</td></tr>
                        <tr><td className="py-2 px-4 font-mono text-blue-400">statsmodels</td><td className="py-2 px-4">0.14.1</td><td className="py-2 px-4">Contiene el modelo ARIMA para predicciones</td></tr>
                        <tr><td className="py-2 px-4 font-mono text-blue-400">arch</td><td className="py-2 px-4">6.3.0</td><td className="py-2 px-4">Contiene el modelo GARCH para volatilidad</td></tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <div>
                  <h4 className="text-lg font-semibold text-orange-400 mb-2">Ejecutar la aplicación:</h4>
                  <div className="bg-gray-800 rounded p-3 font-mono text-sm border border-gray-700">
                    streamlit run app.py
                  </div>
                </div>

                <div>
                  <h4 className="text-lg font-semibold text-purple-400 mb-2">Estructura de archivos recomendada:</h4>
                  <div className="bg-gray-800 rounded p-3 font-mono text-sm border border-gray-700">
                    <div>tu-proyecto/</div>
                    <div className="ml-4">├── app.py              # Código principal</div>
                    <div className="ml-4">├── requirements.txt    # Dependencias</div>
                    <div className="ml-4">└── README.md          # Documentación (opcional)</div>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-green-900/30 to-emerald-900/30 rounded-lg p-4 border border-green-700/30">
                  <h4 className="font-bold text-green-400 mb-2">💡 Para subir a Streamlit Cloud:</h4>
                  <ol className="list-decimal list-inside space-y-1 text-sm text-gray-300">
                    <li>Sube tu proyecto a GitHub con app.py y requirements.txt</li>
                    <li>Ve a <span className="text-blue-400">share.streamlit.io</span></li>
                    <li>Conecta tu repositorio de GitHub</li>
                    <li>Selecciona el archivo app.py como punto de entrada</li>
                    <li>¡Listo! Tu app estará en línea</li>
                  </ol>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-700 mt-12 py-6">
        <div className="max-w-7xl mx-auto px-4 text-center text-gray-500 text-sm">
          Control Maestro v9.0 | ARIMA + GARCH + Análisis Técnico Institucional
        </div>
      </footer>
    </div>
  );
}

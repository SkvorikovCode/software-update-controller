'use client';

import { useState, useEffect } from 'react';
import { arduinoService } from './services/arduino';

export default function Home() {
  const [ports, setPorts] = useState<string[]>([]);
  const [selectedPort, setSelectedPort] = useState('');
  const [status, setStatus] = useState('Не подключено');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadPorts();
  }, []);

  const loadPorts = async () => {
    try {
      const availablePorts = await arduinoService.listPorts();
      setPorts(availablePorts);
    } catch (error) {
      console.error('Ошибка при загрузке портов:', error);
    }
  };

  const handleConnect = async () => {
    if (!selectedPort) return;
    
    setIsLoading(true);
    try {
      await arduinoService.connect(selectedPort);
      setStatus('Подключено');
    } catch (error) {
      console.error('Ошибка при подключении:', error);
      setStatus('Ошибка подключения');
    }
    setIsLoading(false);
  };

  const handleDisconnect = async () => {
    setIsLoading(true);
    try {
      await arduinoService.disconnect();
      setStatus('Не подключено');
    } catch (error) {
      console.error('Ошибка при отключении:', error);
    }
    setIsLoading(false);
  };

  const handleCheckUpdates = async () => {
    setIsLoading(true);
    try {
      const updateInfo = await arduinoService.checkForUpdates();
      if (updateInfo.available) {
        alert(`Доступна новая версия: ${updateInfo.version}`);
      } else {
        alert('Обновления не найдены');
      }
    } catch (error) {
      console.error('Ошибка при проверке обновлений:', error);
    }
    setIsLoading(false);
  };

  const handleInstallUpdate = async () => {
    setIsLoading(true);
    try {
      const result = await arduinoService.installUpdate();
      alert(result.message);
    } catch (error) {
      console.error('Ошибка при установке обновления:', error);
    }
    setIsLoading(false);
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-center">Arduino Updater</h1>
        
        <div className="bg-gray-800 rounded-lg p-6 shadow-xl mb-8">
          <h2 className="text-2xl font-semibold mb-4">Состояние устройства</h2>
          <div className="flex items-center justify-between bg-gray-700 p-4 rounded-lg">
            <span>Статус:</span>
            <span className={`px-3 py-1 rounded-full ${
              status === 'Подключено' ? 'bg-green-500' : 'bg-red-500'
            }`}>
              {status}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
            <h2 className="text-2xl font-semibold mb-4">Подключение</h2>
            <select 
              className="w-full bg-gray-700 border border-gray-600 rounded-lg p-2 mb-4 text-white"
              value={selectedPort}
              onChange={(e) => setSelectedPort(e.target.value)}
              disabled={isLoading}
            >
              <option value="">Выберите порт</option>
              {ports.map((port, index) => (
                <option key={index} value={port}>
                  {port}
                </option>
              ))}
            </select>
            {status === 'Подключено' ? (
              <button 
                className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg transition-colors"
                onClick={handleDisconnect}
                disabled={isLoading}
              >
                Отключиться
              </button>
            ) : (
              <button 
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition-colors"
                onClick={handleConnect}
                disabled={!selectedPort || isLoading}
              >
                Подключиться
              </button>
            )}
          </div>

          <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
            <h2 className="text-2xl font-semibold mb-4">Обновление</h2>
            <div className="space-y-4">
              <button 
                className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition-colors"
                onClick={handleCheckUpdates}
                disabled={status !== 'Подключено' || isLoading}
              >
                Проверить обновления
              </button>
              <button 
                className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-lg transition-colors"
                onClick={handleInstallUpdate}
                disabled={status !== 'Подключено' || isLoading}
              >
                Установить обновление
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
} 
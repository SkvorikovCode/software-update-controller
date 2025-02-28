import { SerialPort } from 'serialport';
import { ReadlineParser } from '@serialport/parser-readline';

interface PortInfo {
    path: string;
    manufacturer?: string;
    serialNumber?: string;
    pnpId?: string;
    locationId?: string;
    vendorId?: string;
    productId?: string;
}

interface UpdateInfo {
    available: boolean;
    version: string;
}

interface UpdateResult {
    success: boolean;
    message: string;
}

class ArduinoService {
    private port: SerialPort | null = null;
    private parser: ReadlineParser | null = null;

    async listPorts(): Promise<string[]> {
        try {
            const ports = await SerialPort.list();
            return ports.map((port: PortInfo) => port.path);
        } catch (error) {
            console.error('Ошибка при получении списка портов:', error);
            return [];
        }
    }

    async connect(portName: string): Promise<boolean> {
        try {
            this.port = new SerialPort({
                path: portName,
                baudRate: 9600,
            });

            this.parser = this.port.pipe(new ReadlineParser({ delimiter: '\r\n' }));
            
            return new Promise((resolve, reject) => {
                if (!this.port) return reject(new Error('Порт не инициализирован'));

                this.port.on('open', () => {
                    console.log('Соединение установлено');
                    resolve(true);
                });

                this.port.on('error', (err: Error) => {
                    console.error('Ошибка соединения:', err);
                    reject(err);
                });
            });
        } catch (error) {
            console.error('Ошибка при подключении:', error);
            throw error;
        }
    }

    async disconnect(): Promise<boolean> {
        if (this.port && this.port.isOpen) {
            return new Promise((resolve) => {
                if (!this.port) return resolve(false);
                
                this.port.close(() => {
                    console.log('Соединение закрыто');
                    resolve(true);
                });
            });
        }
        return false;
    }

    async checkForUpdates(): Promise<UpdateInfo> {
        // Здесь будет логика проверки обновлений
        // Можно реализовать запрос к серверу обновлений или проверку локальных файлов
        return {
            available: false,
            version: '1.0.0'
        };
    }

    async installUpdate(): Promise<UpdateResult> {
        // Здесь будет логика установки обновлений
        // Можно реализовать загрузку и установку новой прошивки
        return {
            success: false,
            message: 'Функция в разработке'
        };
    }
}

export const arduinoService = new ArduinoService(); 
type Listener = () => void;

class EtlApiEmitter {
    private listeners: Listener[] = [];

    subscribe(listener: Listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    emit(delayMs: number = 1000) {
        setTimeout(() => {
            this.listeners.forEach(l => l());
        }, delayMs);
    }
}

export const etlApiEmitter = new EtlApiEmitter();
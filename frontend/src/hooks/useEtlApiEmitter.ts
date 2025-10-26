type Listener = () => void;

class EtlApiEmitter {
    private listeners: Listener[] = [];

    subscribe(listener: Listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    emit() {
        this.listeners.forEach(l => l());
    }
}

export const etlApiEmitter = new EtlApiEmitter();
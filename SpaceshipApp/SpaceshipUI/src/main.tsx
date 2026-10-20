import { render } from 'preact';
import './tokens.css';
import { Hud } from './Hud';
import { chooseHost } from './host/HostBridge';

const host = chooseHost(); // UI code only ever sees HostBridge
host.onMessage(() => {});
render(<Hud />, document.getElementById('app')!);

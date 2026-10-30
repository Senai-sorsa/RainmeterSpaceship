import { HudPanel } from './kit/HudPanel';
import { Ship } from './kit/Ship';

/** The About block of the System category: the ship mark and the app version the host reported. */
export function About({ version }: { version?: string }) {
  return (
    <HudPanel index="00" title="About CSpace" class="about">
      <div class="about-body">
        <span aria-hidden="true"><Ship lit={['fuselage', 'canopy']} size={64} /></span>
        <p class="label" data-about-version>CSpace {version ? `v${version}` : '(version unknown)'}</p>
        <small>Logs are in the temp folder under spaceship-app; the tray has Open log folder.</small>
      </div>
    </HudPanel>
  );
}

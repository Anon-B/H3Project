#!/bin/zsh
cd /Users/anonpond/H3Project
python3 - <<'PY'
from pathlib import Path
p=Path('/Users/anonpond/H3Project/frontend/src/App.tsx')
s=p.read_text()
s=s.replace('<div className="visibilityRow"><FormControlLabel label="Entities" control={<Switch size="small" checked={p.entityVisible} onChange={e=>p.setEntityVisible(e.target.checked)}/>}/><FormControlLabel label="H3 Cells" control={<Switch size="small" checked={p.h3Visible} onChange={e=>p.setH3Visible(e.target.checked)}/>}</div>', '<Stack className="visibilityRow" direction="row" justifyContent="space-between"><FormControlLabel label="Entities" control={<Switch size="small" checked={p.entityVisible} onChange={e=>p.setEntityVisible(e.target.checked)} />} /><FormControlLabel label="H3 Cells" control={<Switch size="small" checked={p.h3Visible} onChange={e=>p.setH3Visible(e.target.checked)} />} /></Stack>')
p.write_text(s)
print('patched visibility JSX')
PY
docker-compose build frontend && docker-compose up -d frontend
curl -fsS http://localhost:8080/ >/dev/null && echo frontend_ok

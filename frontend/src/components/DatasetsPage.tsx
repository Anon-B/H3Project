import { useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';
import DeleteIcon from '@mui/icons-material/Delete';
import MapOutlinedIcon from '@mui/icons-material/MapOutlined';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import RefreshIcon from '@mui/icons-material/Refresh';
import SaveOutlinedIcon from '@mui/icons-material/SaveOutlined';
import StorageIcon from '@mui/icons-material/Storage';
import { PageHeader, SectionCard, Metric } from './ui';
import { API, apiFetch } from '../lib/api';

type Dataset = {
  dataset_id: number;
  dataset: string;
  data_type: string;
  h3_resolution: number;
  feature_count: number;
  part_count: number;
  boundary_h3_count: number;
  metadata?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
  source?: string;
  owner?: string;
  version?: string;
  source_format?: string;
  geographic_coverage?: Record<string, any>;
  tags?: string[];
  license?: string;
  update_frequency?: string;
  schema?: Record<string, any>;
  lineage?: Record<string, any>;
};

export default function DatasetsPage({
  datasets,
  refresh,
  onViewMap,
  onNew,
  onNotify,
  confirmDelete = true,
}: {
  datasets: Dataset[];
  refresh: () => void;
  onViewMap: (name: string) => void;
  onNew: () => void;
  onNotify: (x: string) => void;
  confirmDelete?: boolean;
}) {
  const [detail, setDetail] = useState<any>(null),
    [loading, setLoading] = useState(false),
    [editing, setEditing] = useState(false),
    [deleteTarget, setDeleteTarget] = useState<any>(null),
    [search, setSearch] = useState('');
  const [name, setName] = useState(''),
    [metadata, setMetadata] = useState('{}');
  const [catalog, setCatalog] = useState<any>({
    source: '',
    owner: '',
    version: '1.0.0',
    source_format: '',
    license: '',
    update_frequency: '',
    tags: '',
    geographic_coverage: '{}',
    schema: '{}',
    lineage: '{}',
  });
  const filtered = useMemo(
    () =>
      datasets.filter(
        (d) =>
          d.dataset.toLowerCase().includes(search.toLowerCase()) ||
          d.data_type.toLowerCase().includes(search.toLowerCase()),
      ),
    [datasets, search],
  );
  const sync = (d: any) => {
    setDetail(d);
    setName(d.name);
    setMetadata(JSON.stringify(d.metadata || {}, null, 2));
    setCatalog({
      source: d.source || '',
      owner: d.owner || '',
      version: d.version || '1.0.0',
      source_format: d.source_format || '',
      license: d.license || '',
      update_frequency: d.update_frequency || '',
      tags: (d.tags || []).join(', '),
      geographic_coverage: JSON.stringify(d.geographic_coverage || {}, null, 2),
      schema: JSON.stringify(d.schema || {}, null, 2),
      lineage: JSON.stringify(d.lineage || {}, null, 2),
    });
  };
  const open = async (id: number) => {
    setLoading(true);
    try {
      const r = await apiFetch(API + '/datasets/' + id);
      const d = await r.json();
      if (!r.ok) throw Error(d.detail || 'Dataset not found');
      sync(d);
      setEditing(false);
    } catch (e) {
      onNotify(e instanceof Error ? e.message : 'Load failed');
    } finally {
      setLoading(false);
    }
  };
  const remove = async (id: number, n: string) => {
    try {
      const r = await apiFetch(API + '/datasets/' + id, { method: 'DELETE' });
      const d = await r.json();
      if (!r.ok) throw Error(d.detail || 'Delete failed');
      if (detail?.dataset_id === id) setDetail(null);
      onNotify('ลบ Dataset ' + n + ' แล้ว');
      refresh();
    } catch (e) {
      onNotify(e instanceof Error ? e.message : 'Delete failed');
    } finally {
      setDeleteTarget(null);
    }
  };
  const save = async () => {
    if (!detail) return;
    let meta: any, g: any, sch: any, lin: any;
    try {
      meta = JSON.parse(metadata);
      g = JSON.parse(catalog.geographic_coverage || '{}');
      sch = JSON.parse(catalog.schema || '{}');
      lin = JSON.parse(catalog.lineage || '{}');
    } catch {
      return onNotify('Metadata / Catalog JSON ไม่ถูกต้อง');
    }
    const payload = {
      name: name.trim(),
      metadata: meta,
      source: catalog.source,
      owner: catalog.owner,
      version: catalog.version,
      source_format: catalog.source_format,
      license: catalog.license,
      update_frequency: catalog.update_frequency,
      tags: String(catalog.tags || '')
        .split(',')
        .map((x: string) => x.trim())
        .filter(Boolean),
      geographic_coverage: g,
      schema: sch,
      lineage: lin,
    };
    try {
      const r = await apiFetch(API + '/datasets/' + detail.dataset_id, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const d = await r.json();
      if (!r.ok) throw Error(d.detail || 'Update failed');
      sync(d);
      setEditing(false);
      onNotify('บันทึก Dataset แล้ว');
      refresh();
    } catch (e) {
      onNotify(e instanceof Error ? e.message : 'Update failed');
    }
  };
  if (detail)
    return (
      <section className="page catalogPage">
        <PageHeader
          eyebrow="DATASET DETAIL"
          title={detail.name}
          description={'Dataset ID ' + detail.dataset_id + ' · ' + (detail.data_type || 'Spatial dataset')}
          actions={
            <>
              <Button startIcon={<ArrowBackIcon />} onClick={() => setDetail(null)}>
                Datasets
              </Button>
              <Button startIcon={<OpenInNewIcon />} onClick={() => onViewMap(detail.name)}>
                View on Map
              </Button>
              <Button variant={editing ? 'outlined' : 'contained'} onClick={() => setEditing(!editing)}>
                {editing ? 'Cancel' : 'Edit'}
              </Button>
              <Tooltip title="Refresh">
                <IconButton onClick={() => open(detail.dataset_id)}>
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Delete">
                <IconButton
                  color="error"
                  onClick={() => {
                    if (confirmDelete) setDeleteTarget(detail);
                    else remove(detail.dataset_id, detail.name);
                  }}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </>
          }
        />
        <div className="metricGrid">
          <Metric label="Entities" value={Number(detail.entity_count || 0).toLocaleString()} icon={<StorageIcon />} />
          <Metric label="Parts" value={Number(detail.part_count || 0).toLocaleString()} />
          <Metric label="Boundary H3" value={Number(detail.boundary_h3_count || 0).toLocaleString()} />
          <Metric label="Source resolution" value={'Res ' + detail.h3_resolution} />
        </div>
        <div className="contentGrid">
          <SectionCard title="Dataset configuration" subtitle="Core spatial configuration">
            {editing ? (
              <div className="formGrid">
                <TextField size="small" label="Dataset name" value={name} onChange={(e) => setName(e.target.value)} />
                <TextField size="small" label="H3 Resolution" value={'Res ' + detail.h3_resolution} disabled />
              </div>
            ) : (
              <div className="detailGrid">
                <div>
                  <span>Type</span>
                  <b>{detail.data_type}</b>
                </div>
                <div>
                  <span>H3 Resolution</span>
                  <b>Res {detail.h3_resolution}</b>
                </div>
                <div>
                  <span>Storage</span>
                  <b>{detail.storage_mode || 'boundary_h3'}</b>
                </div>
                <div>
                  <span>Created</span>
                  <b>{String(detail.created_at || '').slice(0, 19) || '—'}</b>
                </div>
                <div>
                  <span>Updated</span>
                  <b>{String(detail.updated_at || '').slice(0, 19) || '—'}</b>
                </div>
              </div>
            )}
            {editing && (
              <Alert severity="info" sx={{ mt: 1 }}>
                Resolution ถูกล็อก เพราะเปลี่ยนแล้วต้อง rebuild H3 coverage
              </Alert>
            )}
          </SectionCard>
          <SectionCard
            title="Metadata"
            subtitle="Dataset-level JSON"
            actions={
              editing && (
                <Button startIcon={<SaveOutlinedIcon />} onClick={save}>
                  Save
                </Button>
              )
            }
          >
            {editing ? (
              <TextField
                multiline
                minRows={8}
                fullWidth
                value={metadata}
                onChange={(e) => setMetadata(e.target.value)}
              />
            ) : (
              <pre className="jsonBox">{JSON.stringify(detail.metadata || {}, null, 2)}</pre>
            )}
          </SectionCard>
        </div>
        <SectionCard
          title="Data catalog"
          subtitle="Provenance · ownership · schema · lineage"
          actions={
            editing && (
              <Button variant="contained" startIcon={<SaveOutlinedIcon />} onClick={save}>
                Save catalog
              </Button>
            )
          }
        >
          {editing ? (
            <div className="catalogForm">
              {[
                ['Source', 'source'],
                ['Owner', 'owner'],
                ['Version', 'version'],
                ['Source Format', 'source_format'],
                ['License', 'license'],
                ['Update Frequency', 'update_frequency'],
                ['Tags', 'tags'],
              ].map(([l, k]: any) => (
                <TextField
                  key={k}
                  size="small"
                  label={l}
                  value={catalog[k]}
                  onChange={(e) => setCatalog({ ...catalog, [k]: e.target.value })}
                />
              ))}
              <TextField
                multiline
                minRows={3}
                size="small"
                label="Geographic Coverage"
                value={catalog.geographic_coverage}
                onChange={(e) => setCatalog({ ...catalog, geographic_coverage: e.target.value })}
              />
              <TextField
                multiline
                minRows={3}
                size="small"
                label="Schema"
                value={catalog.schema}
                onChange={(e) => setCatalog({ ...catalog, schema: e.target.value })}
              />
              <TextField
                multiline
                minRows={3}
                size="small"
                label="Lineage"
                value={catalog.lineage}
                onChange={(e) => setCatalog({ ...catalog, lineage: e.target.value })}
              />
            </div>
          ) : (
            <div className="catalogGrid">
              {[
                ['Source', detail.source],
                ['Owner', detail.owner],
                ['Version', detail.version],
                ['Format', detail.source_format],
                ['License', detail.license],
                ['Update Frequency', detail.update_frequency],
                ['Tags', (detail.tags || []).join(', ') || '—'],
              ].map(([k, v]: any) => (
                <div key={k}>
                  <span>{k}</span>
                  <b>{v || '—'}</b>
                </div>
              ))}
              <div>
                <span>Geographic Coverage</span>
                <pre className="jsonBox">{JSON.stringify(detail.geographic_coverage || {}, null, 2)}</pre>
              </div>
              <div>
                <span>Schema</span>
                <pre className="jsonBox">{JSON.stringify(detail.schema || {}, null, 2)}</pre>
              </div>
              <div>
                <span>Lineage</span>
                <pre className="jsonBox">{JSON.stringify(detail.lineage || {}, null, 2)}</pre>
              </div>
            </div>
          )}
        </SectionCard>
        <Dialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)}>
          <DialogTitle>Delete dataset?</DialogTitle>
          <DialogContent>
            This removes <b>{deleteTarget?.name}</b> and its associated spatial data.
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
            <Button
              color="error"
              variant="contained"
              onClick={() => remove(deleteTarget.dataset_id, deleteTarget.name)}
            >
              Delete
            </Button>
          </DialogActions>
        </Dialog>
      </section>
    );
  return (
    <section className="page catalogPage">
      <PageHeader
        eyebrow="DATA CATALOG"
        title="Datasets"
        description="ค้นหา สำรวจ metadata และเปิด dataset บน Map"
        actions={
          <>
            <Button startIcon={<RefreshIcon />} onClick={refresh}>
              Refresh
            </Button>
            <Button variant="contained" startIcon={<CloudUploadOutlinedIcon />} onClick={onNew}>
              New Dataset
            </Button>
          </>
        }
      />
      <SectionCard
        title="Dataset registry"
        subtitle={filtered.length + ' of ' + datasets.length + ' datasets'}
        actions={
          <TextField
            size="small"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search dataset or type…"
            sx={{ width: 260 }}
          />
        }
      >
        {filtered.length ? (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Dataset</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Resolution</TableCell>
                <TableCell>Entities</TableCell>
                <TableCell>Boundary H3</TableCell>
                <TableCell>Updated</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filtered.map((d) => (
                <TableRow hover key={d.dataset_id}>
                  <TableCell>
                    <b>{d.dataset}</b>
                    <div className="tableSub">{d.source_format || d.data_type}</div>
                  </TableCell>
                  <TableCell>{d.data_type}</TableCell>
                  <TableCell>
                    <Chip size="small" label={'Res ' + d.h3_resolution} />
                  </TableCell>
                  <TableCell>{Number(d.feature_count || 0).toLocaleString()}</TableCell>
                  <TableCell>{Number(d.boundary_h3_count || 0).toLocaleString()}</TableCell>
                  <TableCell>{String(d.updated_at || '').slice(0, 19) || '—'}</TableCell>
                  <TableCell align="right">
                    <Tooltip title="Open">
                      <IconButton onClick={() => open(d.dataset_id)}>
                        <OpenInNewIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="View on map">
                      <IconButton onClick={() => onViewMap(d.dataset)}>
                        <MapOutlinedIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton
                        color="error"
                        onClick={() => {
                          if (confirmDelete) setDeleteTarget(d);
                          else remove(d.dataset_id, d.dataset);
                        }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <div className="emptyState">
            <StorageIcon />
            <b>No datasets found</b>
            <span>ลองเปลี่ยนคำค้น หรือสร้าง Dataset ใหม่</span>
          </div>
        )}
      </SectionCard>
      <LinearProgress sx={{ opacity: loading ? 1 : 0 }} />
      <Dialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Delete dataset?</DialogTitle>
        <DialogContent>
          This removes <b>{deleteTarget?.name || deleteTarget?.dataset}</b> and its associated spatial data.
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button
            color="error"
            variant="contained"
            onClick={() => remove(deleteTarget.dataset_id, deleteTarget.name || deleteTarget.dataset)}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </section>
  );
}

import React, { useState, useEffect, useCallback } from 'react';
import { ViewState, SortConfig, ItemData, UserData, BarcodeData, AuditData } from './admin/types';
import { MainDashboardView, ItemsView, UsersView, BarcodesView, AuditsView, StatCard } from './admin/Views';
import { AddUserModal, type AddUserPayload } from './admin/AddUserModal';
import { ImportUserModal, type ImportUserPayload } from './admin/ImportUserModal';
import { systemStats, measurementUnits } from './admin/mockData';

// Refactored Components (unchanged)
import { ThemeSwitcher } from './admin/ThemeSwitcher';
import { ThemeBackground } from './admin/ThemeBackground';
import { BottomNav } from './admin/BottomNav';
import { AdminStyles } from './admin/AdminStyles';

// Assets (figma:asset stubbed to "" by vite plugin — degrades gracefully)
import imgChar1 from 'figma:asset/31f0d8880b055017fbef8a5361969aaff9dc6b1d.png';
import imgChar2 from 'figma:asset/6ca83cd46c7ec987005a93784c0ea5cb0ea7b153.png';
import imgChar3 from 'figma:asset/52d8dbb8ee8ac80e6c9a5f33b02b197045c3ee7a.png';
import imgChar4 from 'figma:asset/91065b704a188c52c83d5c41934e604d91feb625.png';
import imgChar6 from 'figma:asset/7c350289b4e186e7aee325ab9d0d388d3f3e3e87.png';
import imgChar7 from 'figma:asset/4d4d5a0b21b4ffec3922974bbfa4df54174c8e74.png';
import imgChar8 from 'figma:asset/9734dea3a3cabe5e7e0368c92255d387260d9023.png';
import imgChar9 from 'figma:asset/ad158553f4de3114cdc0729d5c53ae9283e84f61.png';

// API Services
import { fetchStats, fetchUomStats } from '../../services/dashboardService';
import { fetchItems, fetchBarcodes, fetchAudits, deleteAudit, deleteWarehouseAudits } from '../../services/inventoryService';
import { fetchUsers, createUser, deleteUser, fetchOdooCandidates, importOdooUser, type OdooCandidate } from '../../services/adminService';
import { fetchWarehousesAuth, type Warehouse } from '../../services/warehouseService';
import { getUser, isAuthenticated } from '../../services/apiClient';
import { useNavigate } from 'react-router';

const FIGURES = [imgChar1, imgChar2, imgChar3, imgChar4, imgChar6, imgChar7, imgChar8, imgChar9];

/** Build stat cards from real API data, using mock shape/styles */
const buildStatCards = (
  totalItems: number,
  totalBarcodes: number,
  totalAudits: number,
  uomCount: number
): StatCard[] => [
  { ...systemStats[0], value: totalItems.toLocaleString('ar-SA') },
  { ...systemStats[1], value: String(uomCount) },
  { ...systemStats[2], value: totalBarcodes.toLocaleString('ar-SA') },
  { ...systemStats[3], value: totalAudits.toLocaleString('ar-SA') },
];

export function AdminDashboard() {
  const navigate = useNavigate();

  /** Redirect to login if not authenticated */
  useEffect(() => {
    if (!isAuthenticated()) void navigate('/', { replace: true });
  }, [navigate]);

  // ── View / Theme / Sort state ──────────────────────────────────────────────
  const [activeView, setActiveView]         = useState<ViewState>('main');
  const [isPurpleTheme, setIsPurpleTheme]   = useState(false);
  const [selectedFigure, setSelectedFigure] = useState<number>(0);
  const [sortConfig, setSortConfig]         = useState<SortConfig>({ key: 'id', dir: 'none' });

  // ── Main view data ─────────────────────────────────────────────────────────
  const [statCards, setStatCards] = useState<StatCard[]>(systemStats);
  const [uomRows, setUomRows]     = useState(measurementUnits);

  // ── Sub-view data ──────────────────────────────────────────────────────────
  const [items, setItems]       = useState<ItemData[]>([]);
  const [users, setUsers]       = useState<UserData[]>([]);
  const [barcodes, setBarcodes] = useState<BarcodeData[]>([]);
  const [audits, setAudits]     = useState<AuditData[]>([]);

  // ── Add-user modal state ───────────────────────────────────────────────────
  const [showAddUser, setShowAddUser]         = useState(false);
  const [addUserLoading, setAddUserLoading]   = useState(false);
  const [addUserError, setAddUserError]       = useState('');
  const [warehouses, setWarehouses]           = useState<Warehouse[]>([]);

  // ── Import-user modal state ────────────────────────────────────────────────
  const [showImportUser, setShowImportUser]         = useState(false);
  const [importUserLoading, setImportUserLoading]   = useState(false);
  const [importUserError, setImportUserError]       = useState('');
  const [odooCandidates, setOdooCandidates]         = useState<OdooCandidate[]>([]);
  const [candidatesLoading, setCandidatesLoading]   = useState(false);

  // ── Handlers ───────────────────────────────────────────────────────────────
  const handleViewChange = (view: ViewState) => {
    setActiveView(view);
    setSortConfig({ key: 'id', dir: 'none' });
  };

  const handleSortClick = (key: string) => {
    setSortConfig((prev) => {
      if (prev.key !== key) return { key, dir: 'asc' };
      const next = prev.dir === 'none' ? 'asc' : prev.dir === 'asc' ? 'desc' : 'none';
      return { key, dir: next };
    });
  };

  /** Load main dashboard stats on mount */
  const loadMainData = useCallback(async () => {
    const [statsData, uomData] = await Promise.all([fetchStats(), fetchUomStats()]);
    if (statsData) {
      setStatCards(buildStatCards(
        statsData.total_items,
        statsData.total_barcodes,
        statsData.total_audits,
        statsData.uom_count,
      ));
    }
    if (uomData.length) setUomRows(uomData);
  }, []);

  useEffect(() => { void loadMainData(); }, [loadMainData]);

  /** Load warehouses once for the add-user modal */
  useEffect(() => {
    fetchWarehousesAuth()
      .then((list) => {
        const numbered = list.filter((w) => w.name !== 'My Company' && w.code !== 'WH');
        setWarehouses(numbered.length ? numbered : list);
      })
      .catch(() => {});
  }, []);

  /** Load sub-view data when view changes */
  useEffect(() => {
    if (activeView === 'items') {
      fetchItems(1, 50).then((r) => setItems(r.items)).catch(() => {});
    } else if (activeView === 'users') {
      fetchUsers(1, 25).then((r) => setUsers(r.users)).catch(() => {});
    } else if (activeView === 'barcodes') {
      fetchBarcodes(1, 50).then((r) => setBarcodes(r.barcodes)).catch(() => {});
    } else if (activeView === 'audits') {
      fetchAudits({ page: 1, per_page: 25 }).then((r) => setAudits(r.audits)).catch(() => {});
    }
  }, [activeView]);

  /** Open add-user modal */
  const handleOpenAddUser = () => {
    setAddUserError('');
    setShowAddUser(true);
  };

  /** Open import-user modal and fetch Odoo candidates */
  const handleOpenImportUser = async () => {
    setImportUserError('');
    setCandidatesLoading(true);
    setShowImportUser(true);
    try {
      const list = await fetchOdooCandidates();
      setOdooCandidates(list);
    } catch {
      setImportUserError('فشل تحميل مستخدمي أودو');
    } finally {
      setCandidatesLoading(false);
    }
  };

  /** Submit new user to Odoo and refresh the users list */
  const handleAddUser = async (payload: AddUserPayload) => {
    setAddUserLoading(true);
    setAddUserError('');
    try {
      const newUser = await createUser(payload);
      setUsers((prev) => [newUser, ...prev]);
      setShowAddUser(false);
    } catch (err: unknown) {
      setAddUserError((err as { message?: string })?.message ?? 'فشل إنشاء المستخدم');
    } finally {
      setAddUserLoading(false);
    }
  };

  /** Import existing Odoo user into inventory system */
  const handleImportUser = async (payload: ImportUserPayload) => {
    setImportUserLoading(true);
    setImportUserError('');
    try {
      const newUser = await importOdooUser(payload);
      setUsers((prev) => [newUser, ...prev]);
      // Remove imported candidate from list
      setOdooCandidates((prev) => prev.filter((c) => c.id !== payload.odoo_user_id));
      setShowImportUser(false);
    } catch (err: unknown) {
      setImportUserError((err as { message?: string })?.message ?? 'فشل الاستيراد');
    } finally {
      setImportUserLoading(false);
    }
  };

  /** Handle delete operations */
  const handleDeleteAudit = async (id: number) => {
    if (!confirm('هل تريد حذف هذا الجرد؟')) return;
    await deleteAudit(id);
    setAudits((prev) => prev.filter((a) => a.id !== id));
  };

  const handleDeleteUser = async (id: number) => {
    if (!confirm('هل تريد حذف هذا المستخدم؟')) return;
    await deleteUser(id);
    setUsers((prev) => prev.filter((u) => u.id !== id));
  };

  const handleDeleteBarcode = async (id: number) => {
    if (!confirm('هل تريد حذف هذا الباركود؟')) return;
    setBarcodes((prev) => prev.filter((b) => b.id !== id));
  };

  const handleDeleteWarehouseAudits = async () => {
    const user = getUser<{ warehouse_id: number }>();
    if (!user?.warehouse_id || !confirm('حذف كل جردات المخزن الحالي؟')) return;
    await deleteWarehouseAudits(user.warehouse_id);
    void loadMainData();
  };

  const handleDeleteAllAudits = async () => {
    if (!confirm('تحذير: سيتم حذف كل الجردات! هل أنت متأكد؟')) return;
    void loadMainData();
  };

  return (
    <div dir="rtl" className={`min-h-screen bg-[#05060A] text-slate-300 font-sans pb-32 pt-8 selection:bg-purple-500/30 transition-colors duration-500 ${isPurpleTheme ? 'theme-purple' : ''}`}>
      
      {/* Dynamic Theme Components — unchanged */}
      <ThemeSwitcher 
        isPurpleTheme={isPurpleTheme} 
        onToggle={() => setIsPurpleTheme(!isPurpleTheme)} 
      />
      <ThemeBackground 
        isPurpleTheme={isPurpleTheme} 
        selectedFigure={selectedFigure} 
        onSelectFigure={setSelectedFigure}
        figures={FIGURES} 
      />

      {/* Main Content Areas */}
      <main className="container mx-auto px-4 max-w-[1200px] space-y-6 relative z-10">
        {activeView === 'main' && (
          <MainDashboardView
            onViewChange={handleViewChange}
            stats={statCards}
            uomStats={uomRows}
            onDeleteWarehouseAudits={() => void handleDeleteWarehouseAudits()}
            onDeleteAllAudits={() => void handleDeleteAllAudits()}
          />
        )}
        {activeView === 'items' && (
          <ItemsView
            onViewChange={handleViewChange}
            sortConfig={sortConfig}
            onSortClick={handleSortClick}
            items={items}
          />
        )}
        {activeView === 'users' && (
          <UsersView
            onViewChange={handleViewChange}
            sortConfig={sortConfig}
            onSortClick={handleSortClick}
            users={users}
            onDeleteUser={(id) => void handleDeleteUser(id)}
            onAddUser={handleOpenAddUser}
            onImportUser={() => void handleOpenImportUser()}
          />
        )}
        {activeView === 'barcodes' && (
          <BarcodesView
            onViewChange={handleViewChange}
            sortConfig={sortConfig}
            onSortClick={handleSortClick}
            barcodes={barcodes}
            onDeleteBarcode={(id) => void handleDeleteBarcode(id)}
          />
        )}
        {activeView === 'audits' && (
          <AuditsView
            onViewChange={handleViewChange}
            sortConfig={sortConfig}
            onSortClick={handleSortClick}
            audits={audits}
            onDeleteAudit={(id) => void handleDeleteAudit(id)}
          />
        )}
      </main>

      {/* Layout Components — unchanged */}
      <BottomNav />
      <AdminStyles />

      {/* Add User Modal */}
      {showAddUser && (
        <AddUserModal
          warehouses={warehouses}
          loading={addUserLoading}
          error={addUserError}
          onClose={() => setShowAddUser(false)}
          onSubmit={(payload) => void handleAddUser(payload)}
        />
      )}

      {/* Import User Modal */}
      {showImportUser && (
        <ImportUserModal
          candidates={candidatesLoading ? [] : odooCandidates}
          warehouses={warehouses}
          loading={importUserLoading || candidatesLoading}
          error={importUserError}
          onClose={() => setShowImportUser(false)}
          onSubmit={(payload) => void handleImportUser(payload)}
        />
      )}
    </div>
  );
}

import { useEffect, useState } from 'react'
import {
  cleanupAdminDuplicates,
  createAdminDocument,
  deleteAdminDocument,
  deleteAdminInteraction,
  deleteAdminRating,
  deleteAdminSearchRecord,
  deleteAdminUser,
  downloadAdminBackup,
  downloadAdminExport,
  getAdminCatalogOptions,
  getAdminDocument,
  getAdminDocuments,
  getAdminInteractions,
  getAdminLogs,
  getAdminOverview,
  getAdminRatings,
  getAdminRecommendationDiagnostics,
  getAdminSearchHistory,
  getAdminUser,
  getAdminUsers,
  importAdminDocuments,
  importDvfuDocuments,
  mergeAdminDocuments,
  updateAdminDocument,
  updateAdminUser,
} from '../api/admin'

type AdminDocumentForm = {
  title: string
  authors: string
  year: string
  abstract: string
  keywords: string
  category: string
}

const emptyDocumentForm: AdminDocumentForm = {
  title: '',
  authors: '',
  year: '',
  abstract: '',
  keywords: '',
  category: '',
}

function saveBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(url)
}

export default function AdminPage() {
  const [overview, setOverview] = useState<any>(null)
  const [documents, setDocuments] = useState<any[]>([])
  const [catalogOptions, setCatalogOptions] = useState<any>({ categories: [], authors: [], years: [] })
  const [users, setUsers] = useState<any[]>([])
  const [selectedUserProfile, setSelectedUserProfile] = useState<any>(null)
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
  const [interactions, setInteractions] = useState<any[]>([])
  const [ratings, setRatings] = useState<any[]>([])
  const [searchHistory, setSearchHistory] = useState<any[]>([])
  const [logs, setLogs] = useState<any>(null)
  const [recommendationDiagnostics, setRecommendationDiagnostics] = useState<any>(null)
  const [selectedDocument, setSelectedDocument] = useState<any>(null)
  const [documentForm, setDocumentForm] = useState<AdminDocumentForm>(emptyDocumentForm)
  const [editingDocumentId, setEditingDocumentId] = useState<number | null>(null)
  const [documentFilters, setDocumentFilters] = useState({
    search: '',
    category: '',
    author: '',
    year: '',
  })
  const [interactionFilters, setInteractionFilters] = useState({
    user_id: '',
    document_id: '',
    interaction_type: '',
    query: '',
  })
  const [mergeSourceId, setMergeSourceId] = useState('')
  const [mergeTargetId, setMergeTargetId] = useState('')
  const [dvfuImportQuery, setDvfuImportQuery] = useState('химия')
  const [dvfuImportPages, setDvfuImportPages] = useState('1')
  const [dvfuImportLimit, setDvfuImportLimit] = useState('50')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const loadOverview = async () => {
    const data = await getAdminOverview()
    setOverview(data)
  }

  const loadDocuments = async () => {
    const params: Record<string, string | number> = {}
    if (documentFilters.search.trim()) params.search = documentFilters.search.trim()
    if (documentFilters.category.trim()) params.category = documentFilters.category.trim()
    if (documentFilters.author.trim()) params.author = documentFilters.author.trim()
    if (documentFilters.year.trim()) params.year = Number(documentFilters.year)
    const data = await getAdminDocuments(params)
    setDocuments(data)
  }

  const loadUsers = async () => {
    const data = await getAdminUsers()
    setUsers(data)
  }

  const loadModerationData = async () => {
    const interactionParams: Record<string, string | number> = {}
    const ratingParams: Record<string, string | number> = {}
    const searchParams: Record<string, string | number> = {}

    if (interactionFilters.user_id.trim()) {
      interactionParams.user_id = Number(interactionFilters.user_id)
      ratingParams.user_id = Number(interactionFilters.user_id)
      searchParams.user_id = Number(interactionFilters.user_id)
    }
    if (interactionFilters.document_id.trim()) {
      interactionParams.document_id = Number(interactionFilters.document_id)
      ratingParams.document_id = Number(interactionFilters.document_id)
    }
    if (interactionFilters.interaction_type.trim()) {
      interactionParams.interaction_type = interactionFilters.interaction_type
    }
    if (interactionFilters.query.trim()) {
      searchParams.query = interactionFilters.query
    }

    const [interactionsData, ratingsData, searchData] = await Promise.all([
      getAdminInteractions(interactionParams),
      getAdminRatings(ratingParams),
      getAdminSearchHistory(searchParams),
    ])

    setInteractions(interactionsData)
    setRatings(ratingsData)
    setSearchHistory(searchData)
  }

  const loadLogs = async () => {
    const data = await getAdminLogs()
    setLogs(data)
  }

  const loadInitialData = async () => {
    setLoading(true)
    setError('')
    try {
      const [overviewData, optionsData, documentsData, usersData, interactionsData, ratingsData, searchData, logsData] =
        await Promise.all([
          getAdminOverview(),
          getAdminCatalogOptions(),
          getAdminDocuments(),
          getAdminUsers(),
          getAdminInteractions(),
          getAdminRatings(),
          getAdminSearchHistory(),
          getAdminLogs(),
        ])

      setOverview(overviewData)
      setCatalogOptions(optionsData)
      setDocuments(documentsData)
      setUsers(usersData)
      setInteractions(interactionsData)
      setRatings(ratingsData)
      setSearchHistory(searchData)
      setLogs(logsData)
    } catch (err: any) {
      console.error(err)
      setError(err?.response?.data?.detail || 'Не удалось загрузить данные админки')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    if (selectedUserId === null && users.length > 0) {
      const firstNonAdmin = users.find((user) => user.role !== 'admin') || users[0]
      if (firstNonAdmin) {
        setSelectedUserId(firstNonAdmin.id)
      }
    }
  }, [users, selectedUserId])

  useEffect(() => {
    if (selectedUserId === null) return
    getAdminUser(selectedUserId)
      .then(setSelectedUserProfile)
      .catch((err) => {
        console.error(err)
      })
  }, [selectedUserId])

  const resetDocumentForm = () => {
    setEditingDocumentId(null)
    setDocumentForm(emptyDocumentForm)
    setSelectedDocument(null)
  }

  const handleDocumentFormChange = (field: keyof AdminDocumentForm, value: string) => {
    setDocumentForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleDocumentSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setMessage('')
    setError('')

    try {
      const payload = {
        ...documentForm,
        year: Number(documentForm.year),
        abstract: documentForm.abstract || null,
        keywords: documentForm.keywords || null,
        category: documentForm.category || null,
      }

      if (editingDocumentId !== null) {
        await updateAdminDocument(editingDocumentId, payload)
        setMessage(`Документ ${editingDocumentId} обновлен`)
      } else {
        await createAdminDocument(payload)
        setMessage('Документ добавлен')
      }

      resetDocumentForm()
      await Promise.all([loadDocuments(), loadOverview(), loadLogs()])
    } catch (err: any) {
      console.error(err)
      setError(err?.response?.data?.detail || 'Не удалось сохранить документ')
    }
  }

  const handleEditDocument = async (documentId: number) => {
    const document = await getAdminDocument(documentId)
    setSelectedDocument(document)
    setEditingDocumentId(document.id)
    setDocumentForm({
      title: document.title || '',
      authors: document.authors || '',
      year: String(document.year || ''),
      abstract: document.abstract || '',
      keywords: document.keywords || '',
      category: document.category || '',
    })
  }

  const handleDeleteDocument = async (documentId: number) => {
    await deleteAdminDocument(documentId)
    if (editingDocumentId === documentId) {
      resetDocumentForm()
    }
    await Promise.all([loadDocuments(), loadOverview(), loadModerationData(), loadLogs()])
    setMessage(`Документ ${documentId} удален`)
  }

  const handleImportDocuments = async () => {
    const result = await importAdminDocuments()
    await Promise.all([loadDocuments(), loadOverview()])
    setMessage(`Импорт завершен. Добавлено: ${result.imported}`)
  }

  const handleImportDvfuDocuments = async () => {
    const result = await importDvfuDocuments({
      query: dvfuImportQuery,
      pages: Number(dvfuImportPages) || 1,
      max_records: Number(dvfuImportLimit) || 50,
    })
    await Promise.all([loadDocuments(), loadOverview()])
    setMessage(
      `Импорт ДВФУ завершен. Найдено ссылок: ${result.urls_found}, добавлено: ${result.imported}, обновлено: ${result.updated}, пропущено: ${result.skipped}`
    )
  }

  const handleMergeDocuments = async () => {
    if (!mergeSourceId || !mergeTargetId) return
    const result = await mergeAdminDocuments(Number(mergeSourceId), Number(mergeTargetId))
    setMergeSourceId('')
    setMergeTargetId('')
    resetDocumentForm()
    await Promise.all([loadDocuments(), loadOverview(), loadModerationData(), loadLogs()])
    setMessage(result.message)
  }

  const handleUserRoleChange = async (userId: number, role: string) => {
    await updateAdminUser(userId, { role })
    await Promise.all([loadUsers(), selectedUserId === userId ? getAdminUser(userId).then(setSelectedUserProfile) : Promise.resolve()])
    setMessage(`Роль пользователя ${userId} обновлена`)
  }

  const handleUserBlockToggle = async (userId: number, isBlocked: boolean) => {
    await updateAdminUser(userId, { is_blocked: !isBlocked })
    await Promise.all([loadUsers(), selectedUserId === userId ? getAdminUser(userId).then(setSelectedUserProfile) : Promise.resolve()])
    setMessage(`Статус блокировки пользователя ${userId} обновлен`)
  }

  const handleDeleteUser = async (userId: number) => {
    await deleteAdminUser(userId)
    if (selectedUserId === userId) {
      setSelectedUserId(null)
      setSelectedUserProfile(null)
    }
    await Promise.all([loadUsers(), loadOverview(), loadModerationData(), loadLogs()])
    setMessage(`Пользователь ${userId} удален`)
  }

  const handleDiagnosticsLoad = async () => {
    if (selectedUserId === null) return
    const data = await getAdminRecommendationDiagnostics(selectedUserId)
    setRecommendationDiagnostics(data)
  }

  const handleCleanupDuplicates = async () => {
    const result = await cleanupAdminDuplicates()
    await Promise.all([loadModerationData(), loadLogs(), loadOverview()])
    setMessage(
      `Очистка завершена: favorite ${result.removed_favorite_duplicates}, view ${result.merged_view_duplicates}, search ${result.removed_search_duplicates}`
    )
  }

  const handleDownload = async (kind: 'documents' | 'users' | 'history' | 'backup') => {
    const blob =
      kind === 'backup' ? await downloadAdminBackup() : await downloadAdminExport(kind)
    const filename =
      kind === 'backup'
        ? 'backup.json'
        : kind === 'documents'
          ? 'documents.csv'
          : kind === 'users'
            ? 'users.csv'
            : 'history.csv'
    saveBlob(blob, filename)
  }

  if (loading) {
    return <p>Загрузка админки...</p>
  }

  return (
    <div className="content-stack">
      <h1 className="page-title">Админка</h1>

      {message && <div className="auth-message success">{message}</div>}
      {error && <div className="auth-message error">{error}</div>}

      <section className="content-section">
        <div className="section-head">
          <h2>Сводка</h2>
          <p>Ключевые метрики системы и самые активные материалы</p>
        </div>

        <div className="profile-stats-grid">
          <div className="stat-card"><div className="stat-value">{overview?.counts?.documents ?? 0}</div><div className="stat-label">Документов</div></div>
          <div className="stat-card"><div className="stat-value">{overview?.counts?.users ?? 0}</div><div className="stat-label">Пользователей</div></div>
          <div className="stat-card"><div className="stat-value">{overview?.counts?.views ?? 0}</div><div className="stat-label">Просмотров</div></div>
          <div className="stat-card"><div className="stat-value">{overview?.counts?.ratings ?? 0}</div><div className="stat-label">Оценок</div></div>
        </div>

        <div className="admin-columns" style={{ marginTop: '20px' }}>
          <div className="card">
            <h3>Популярные документы</h3>
            {(overview?.popular_documents ?? []).map((item: any) => (
              <p key={item.id}>{item.title} ({item.interactions_count})</p>
            ))}
          </div>
          <div className="card">
            <h3>Популярные категории</h3>
            {(overview?.popular_categories ?? []).map((item: any) => (
              <p key={item.category}>{item.category} ({item.interactions_count})</p>
            ))}
          </div>
          <div className="card">
            <h3>Чаще в избранном</h3>
            {(overview?.favorite_documents ?? []).map((item: any) => (
              <p key={item.id}>{item.title} ({item.favorites_count})</p>
            ))}
          </div>
        </div>

        <div className="card" style={{ marginTop: '20px' }}>
          <h3>Аналитика по категориям</h3>
          <p>Сводка по просмотрам документов: сколько пользователей смотрели разные темы.</p>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Категория</th>
                  <th>Документов</th>
                  <th>Пользователей</th>
                  <th>Просмотров</th>
                </tr>
              </thead>
              <tbody>
                {(overview?.category_view_analytics ?? []).map((item: any) => (
                  <tr key={item.category}>
                    <td>{item.category}</td>
                    <td>{item.documents_count}</td>
                    <td>{item.unique_viewers}</td>
                    <td>{item.views_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="content-section">
        <div className="section-head">
          <h2>Документы и каталог</h2>
          <p>Добавление, редактирование, импорт CSV, фильтры и объединение дублей</p>
        </div>

        <div className="admin-toolbar">
          <input value={documentFilters.search} onChange={(e) => setDocumentFilters((prev) => ({ ...prev, search: e.target.value }))} placeholder="Поиск" />
          <input value={documentFilters.category} onChange={(e) => setDocumentFilters((prev) => ({ ...prev, category: e.target.value }))} placeholder="Категория" list="admin-categories" />
          <input value={documentFilters.author} onChange={(e) => setDocumentFilters((prev) => ({ ...prev, author: e.target.value }))} placeholder="Автор" list="admin-authors" />
          <input value={documentFilters.year} onChange={(e) => setDocumentFilters((prev) => ({ ...prev, year: e.target.value }))} placeholder="Год" />
          <button onClick={loadDocuments}>Фильтровать</button>
          <button onClick={handleImportDocuments}>Импорт CSV</button>
          <button onClick={resetDocumentForm} className="auth-secondary-link">Новый документ</button>
        </div>

        <div className="admin-toolbar">
          <input value={dvfuImportQuery} onChange={(e) => setDvfuImportQuery(e.target.value)} placeholder="Запрос ДВФУ" />
          <input value={dvfuImportPages} onChange={(e) => setDvfuImportPages(e.target.value)} placeholder="Страниц" />
          <input value={dvfuImportLimit} onChange={(e) => setDvfuImportLimit(e.target.value)} placeholder="Лимит записей" />
          <button onClick={handleImportDvfuDocuments}>Импорт из ДВФУ</button>
        </div>

        <datalist id="admin-categories">
          {(catalogOptions.categories ?? []).map((item: string) => <option key={item} value={item} />)}
        </datalist>
        <datalist id="admin-authors">
          {(catalogOptions.authors ?? []).map((item: string) => <option key={item} value={item} />)}
        </datalist>

        <div className="admin-grid-2">
          <form className="admin-form card" onSubmit={handleDocumentSubmit}>
            <h3>{editingDocumentId !== null ? `Редактирование #${editingDocumentId}` : 'Новый документ'}</h3>
            <input value={documentForm.title} onChange={(e) => handleDocumentFormChange('title', e.target.value)} placeholder="Название" required />
            <input value={documentForm.authors} onChange={(e) => handleDocumentFormChange('authors', e.target.value)} placeholder="Авторы" required />
            <input value={documentForm.year} onChange={(e) => handleDocumentFormChange('year', e.target.value)} placeholder="Год" required />
            <input value={documentForm.category} onChange={(e) => handleDocumentFormChange('category', e.target.value)} placeholder="Категория" />
            <input value={documentForm.keywords} onChange={(e) => handleDocumentFormChange('keywords', e.target.value)} placeholder="Ключевые слова" />
            <textarea value={documentForm.abstract} onChange={(e) => handleDocumentFormChange('abstract', e.target.value)} placeholder="Аннотация" rows={6} />
            <button type="submit">{editingDocumentId !== null ? 'Сохранить изменения' : 'Добавить документ'}</button>
          </form>

          <div className="card">
            <h3>Объединение дублей</h3>
            <input value={mergeSourceId} onChange={(e) => setMergeSourceId(e.target.value)} placeholder="ID документа-источника" />
            <input value={mergeTargetId} onChange={(e) => setMergeTargetId(e.target.value)} placeholder="ID документа-приемника" />
            <button onClick={handleMergeDocuments}>Объединить</button>

            {selectedDocument && (
              <div style={{ marginTop: '18px' }}>
                <h3>Полная карточка документа</h3>
                <p><strong>ID:</strong> {selectedDocument.id}</p>
                <p><strong>Название:</strong> {selectedDocument.title}</p>
                <p><strong>Авторы:</strong> {selectedDocument.authors}</p>
                <p><strong>Год:</strong> {selectedDocument.year}</p>
                <p><strong>Категория:</strong> {selectedDocument.category || 'не указана'}</p>
                <p><strong>Ключевые слова:</strong> {selectedDocument.keywords || 'не указаны'}</p>
                <p><strong>Рубрики:</strong> {selectedDocument.rubrics || 'не указаны'}</p>
                <p><strong>Издательство:</strong> {selectedDocument.publisher || 'не указано'}</p>
                <p><strong>ISBN:</strong> {selectedDocument.isbn || 'не указан'}</p>
                <p><strong>УДК:</strong> {selectedDocument.udk || 'не указан'}</p>
                {selectedDocument.source_url && (
                  <p>
                    <strong>Источник:</strong>{' '}
                    <a href={selectedDocument.source_url} target="_blank" rel="noreferrer">карточка ДВФУ</a>
                  </p>
                )}
                <p><strong>Аннотация:</strong> {selectedDocument.abstract || 'нет'}</p>
              </div>
            )}
          </div>
        </div>

        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Название</th>
                <th>Авторы</th>
                <th>Год</th>
                <th>Категория</th>
                <th>Источник</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((document) => (
                <tr key={document.id}>
                  <td>{document.id}</td>
                  <td>{document.title}</td>
                  <td>{document.authors}</td>
                  <td>{document.year}</td>
                  <td>{document.category || '-'}</td>
                  <td>{document.source_system || '-'}</td>
                  <td className="admin-actions">
                    <button onClick={() => handleEditDocument(document.id)}>Открыть</button>
                    <button onClick={() => handleDeleteDocument(document.id)} className="auth-secondary-link">Удалить</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="content-section">
        <div className="section-head">
          <h2>Пользователи и рекомендации</h2>
          <p>Профиль пользователя, блокировка, роли и диагностика рекомендаций</p>
        </div>

        <div className="admin-grid-2">
          <div className="card">
            <h3>Пользователи</h3>
            <div className="admin-table-wrap">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Пользователь</th>
                    <th>Роль</th>
                    <th>Статус</th>
                    <th>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td>{user.id}</td>
                      <td>
                        <button className="admin-inline-button" onClick={() => setSelectedUserId(user.id)}>
                          {user.username}
                        </button>
                      </td>
                      <td>
                        <select value={user.role} onChange={(e) => handleUserRoleChange(user.id, e.target.value)}>
                          <option value="reader">reader</option>
                          <option value="admin">admin</option>
                        </select>
                      </td>
                      <td>{user.is_blocked ? 'blocked' : 'active'}</td>
                      <td className="admin-actions">
                        <button onClick={() => handleUserBlockToggle(user.id, Boolean(user.is_blocked))}>
                          {user.is_blocked ? 'Разблокировать' : 'Блокировать'}
                        </button>
                        {user.username !== 'admin' && (
                          <button onClick={() => handleDeleteUser(user.id)} className="auth-secondary-link">Удалить</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="card">
            <h3>Профиль пользователя</h3>
            {selectedUserProfile ? (
              <>
                <p><strong>ID:</strong> {selectedUserProfile.user.id}</p>
                <p><strong>Username:</strong> {selectedUserProfile.user.username}</p>
                <p><strong>Email:</strong> {selectedUserProfile.user.email}</p>
                <p><strong>Role:</strong> {selectedUserProfile.user.role}</p>
                <p><strong>Status:</strong> {selectedUserProfile.user.is_blocked ? 'blocked' : 'active'}</p>
                <button onClick={handleDiagnosticsLoad}>Проверить рекомендации</button>
                <h3 style={{ marginTop: '18px' }}>Последние действия</h3>
                {selectedUserProfile.recent_interactions.map((item: any) => (
                  <p key={item.id}>{item.document_title} [{item.interaction_type}]</p>
                ))}
                <h3 style={{ marginTop: '18px' }}>Последние запросы</h3>
                {selectedUserProfile.recent_searches.map((item: any) => (
                  <p key={item.id}>{item.query}</p>
                ))}
              </>
            ) : (
              <p>Выберите пользователя.</p>
            )}
          </div>
        </div>

        {recommendationDiagnostics && (
          <div className="admin-columns" style={{ marginTop: '20px' }}>
            <div className="card">
              <h3>Основа рекомендаций</h3>
              {recommendationDiagnostics.source_documents.map((item: any) => (
                <p key={item.id}>{item.title}</p>
              ))}
            </div>
            <div className="card">
              <h3>Content-based</h3>
              {recommendationDiagnostics.content_based.map((item: any) => (
                <p key={item.id}>{item.title} ({item.score})</p>
              ))}
            </div>
            <div className="card">
              <h3>Collaborative</h3>
              {recommendationDiagnostics.collaborative.map((item: any) => (
                <p key={item.id}>{item.title} ({item.score})</p>
              ))}
            </div>
            <div className="card">
              <h3>Hybrid</h3>
              {recommendationDiagnostics.hybrid.map((item: any) => (
                <p key={item.id}>{item.title} ({item.score})</p>
              ))}
            </div>
          </div>
        )}
      </section>

      <section className="content-section">
        <div className="section-head">
          <h2>Взаимодействия и отладка</h2>
          <p>История действий, удаление дублей, логи ошибок и пустые рекомендации</p>
        </div>

        <div className="admin-toolbar">
          <input value={interactionFilters.user_id} onChange={(e) => setInteractionFilters((prev) => ({ ...prev, user_id: e.target.value }))} placeholder="Фильтр user_id" />
          <input value={interactionFilters.document_id} onChange={(e) => setInteractionFilters((prev) => ({ ...prev, document_id: e.target.value }))} placeholder="Фильтр document_id" />
          <input value={interactionFilters.interaction_type} onChange={(e) => setInteractionFilters((prev) => ({ ...prev, interaction_type: e.target.value }))} placeholder="Тип interaction" />
          <input value={interactionFilters.query} onChange={(e) => setInteractionFilters((prev) => ({ ...prev, query: e.target.value }))} placeholder="Поисковый запрос" />
          <button onClick={loadModerationData}>Применить</button>
          <button onClick={handleCleanupDuplicates}>Удалить дубли</button>
          <button onClick={loadLogs} className="auth-secondary-link">Обновить логи</button>
        </div>

        <div className="admin-columns">
          <div className="card">
            <h3>Просмотры и избранное</h3>
            {interactions.map((item) => (
              <div key={item.id} className="small-card">
                <p>{item.username}: {item.document_title} [{item.interaction_type}]</p>
                <button onClick={() => deleteAdminInteraction(item.id).then(loadModerationData)}>Удалить</button>
              </div>
            ))}
          </div>
          <div className="card">
            <h3>Оценки</h3>
            {ratings.map((item) => (
              <div key={item.id} className="small-card">
                <p>{item.username}: {item.document_title} ({item.score}/5)</p>
                <button onClick={() => deleteAdminRating(item.id).then(loadModerationData)}>Удалить</button>
              </div>
            ))}
          </div>
          <div className="card">
            <h3>История поиска</h3>
            {searchHistory.map((item) => (
              <div key={item.id} className="small-card">
                <p>{item.username}: {item.query}</p>
                <button onClick={() => deleteAdminSearchRecord(item.id).then(loadModerationData)}>Удалить</button>
              </div>
            ))}
          </div>
        </div>

        {logs && (
          <div className="admin-columns" style={{ marginTop: '20px' }}>
            <div className="card">
              <h3>Ошибки API</h3>
              {(logs.error_events ?? []).map((item: any, index: number) => (
                <p key={`${item.timestamp}-${index}`}>{item.method} {item.path}: {item.error}</p>
              ))}
            </div>
            <div className="card">
              <h3>Неудачные запросы</h3>
              {(logs.failed_requests ?? []).map((item: any, index: number) => (
                <p key={`${item.timestamp}-${index}`}>{item.status_code} {item.method} {item.path}</p>
              ))}
            </div>
            <div className="card">
              <h3>Пустые рекомендации</h3>
              {(logs.empty_recommendations ?? []).map((item: any) => (
                <p key={item.user_id}>{item.username}</p>
              ))}
            </div>
            <div className="card">
              <h3>Дубли</h3>
              <p>Просмотры: {(logs.duplicate_views ?? []).length}</p>
              <p>Избранное: {(logs.duplicate_favorites ?? []).length}</p>
            </div>
          </div>
        )}
      </section>

      <section className="content-section">
        <div className="section-head">
          <h2>Экспорт и резервные функции</h2>
          <p>CSV-выгрузки и JSON backup базы</p>
        </div>
        <div className="admin-toolbar">
          <button onClick={() => handleDownload('documents')}>Экспорт документов</button>
          <button onClick={() => handleDownload('users')}>Экспорт пользователей</button>
          <button onClick={() => handleDownload('history')}>Экспорт истории</button>
          <button onClick={() => handleDownload('backup')}>Резервная копия</button>
        </div>
      </section>
    </div>
  )
}

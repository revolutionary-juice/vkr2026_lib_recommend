interface Props {
  value: string
  onChange: (value: string) => void
  onSearch: () => void
}

export default function SearchBar({ value, onChange, onSearch }: Props) {
  return (
    <div className="search-bar">
      <input
        type="text"
        placeholder="Поиск по документам..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      <button onClick={onSearch}>Искать</button>
    </div>
  )
}
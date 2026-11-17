import type { Sheet, SheetField, StatRow, Stats, StatValue } from "../../model/types";
import styles from "./StatBlock.module.css";

type Scalar = number | string | undefined;
type Section = Sheet["sections"][number];

/** One value of the sheet, typed over in place; clearing it removes the value. */
function Cell({ field, value, onChange }: { field: SheetField; value: Scalar; onChange: (value: Scalar) => void }) {
  return field.type === "int" ? (
    <input
      className={styles.input}
      type="number"
      inputMode="numeric"
      step={1}
      min={field.min}
      max={field.max}
      value={value ?? ""}
      placeholder="—"
      aria-label={field.label}
      onChange={(event) => onChange(event.target.value === "" ? undefined : Number(event.target.value))}
    />
  ) : (
    // A textarea so long text wraps instead of being cut off; it still holds one line of meaning.
    <textarea
      className={styles.input}
      rows={1}
      maxLength={2000}
      value={value ?? ""}
      placeholder="—"
      aria-label={field.label}
      onChange={(event) => onChange(event.target.value.replace(/\n/g, " ") || undefined)}
    />
  );
}

/** A repeating field, such as skills with a speciality: one row per entry. */
function Rows({ field, rows, onChange }: { field: SheetField; rows: StatRow[]; onChange: (rows: StatRow[]) => void }) {
  const columns = field.itemFields ?? [];
  const setCell = (index: number, key: string, value: Scalar) =>
    onChange(
      rows.map((row, at) => {
        if (at !== index) return row;
        const { [key]: _dropped, ...rest } = row;
        return value === undefined ? rest : { ...rest, [key]: value };
      }),
    );
  return (
    <div className={styles.list}>
      {rows.length > 0 && (
        <table className={styles.table}>
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column.key} scope="col" className={column.type === "int" ? styles.num : undefined}>
                  {column.label}
                </th>
              ))}
              <td />
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              // Rows have no identity of their own; the index is stable while one is edited.
              <tr key={index}>
                {columns.map((column) => (
                  <td key={column.key} className={column.type === "int" ? styles.num : undefined}>
                    <Cell field={column} value={row[column.key]} onChange={(value) => setCell(index, column.key, value)} />
                  </td>
                ))}
                <td className={styles.tool}>
                  <button
                    type="button"
                    className={styles.remove}
                    aria-label={`Remove ${field.label} row ${index + 1}`}
                    onClick={() => onChange(rows.filter((_, at) => at !== index))}
                  >
                    <svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden>
                      <path d="M3.5 3.5l7 7M10.5 3.5l-7 7" strokeLinecap="round" />
                    </svg>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <button type="button" className={styles.addRow} onClick={() => onChange([...rows, {}])}>
        <svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden>
          <path d="M7 2.5v9M2.5 7h9" strokeLinecap="round" />
        </svg>
        Add {field.label.toLowerCase()}
      </button>
    </div>
  );
}

/** A section too wide for half the sheet: a row of many numbers, or a table of many columns. */
const isWide = (section: Section) =>
  section.fields.filter((field) => field.type === "int").length > 4 ||
  section.fields.some((field) => {
    const columns = field.itemFields ?? [];
    // Three columns of writing need the room as much as five of anything.
    return columns.length > 4 || columns.filter((column) => column.type === "text").length > 2;
  });

type StatBlockProps = {
  sheet: Sheet;
  stats: Stats;
  onChange: (stats: Stats) => void;
};

/** The stat block of a character, laid out by the campaign system's sheet (ADR-0030): numbers as
 *  a row of tiles, text as labelled lines, repeating fields as tables. Narrow sections sit two
 *  abreast. */
export function StatBlock({ sheet, stats, onChange }: StatBlockProps) {
  const set = (section: string, key: string, value: StatValue | undefined) => {
    const { [key]: _dropped, ...rest } = stats[section] ?? {};
    onChange({ ...stats, [section]: value === undefined ? rest : { ...rest, [key]: value } });
  };
  return (
    <div className={styles.block}>
      {sheet.sections.map((section) => {
        // Stats saved before the sheet existed can hold any shape here (ADR-0030 NEG-002);
        // what does not fit is shown as empty, never allowed to break the page.
        const saved: unknown = stats[section.key];
        const values = (saved && typeof saved === "object" && !Array.isArray(saved) ? saved : {}) as Stats[string];
        const numbers = section.fields.filter((field) => field.type === "int");
        const texts = section.fields.filter((field) => field.type === "text");
        return (
          <section key={section.key} className={isWide(section) ? styles.wide : styles.section} aria-label={section.label}>
            <h3 className={styles.heading}>{section.label}</h3>
            {numbers.length > 0 && (
              <div className={styles.tiles}>
                {numbers.map((field) => (
                  <label key={field.key} className={styles.tile}>
                    <span className={styles.key}>{field.label}</span>
                    <Cell field={field} value={values[field.key] as Scalar} onChange={(value) => set(section.key, field.key, value)} />
                  </label>
                ))}
              </div>
            )}
            {texts.map((field) => (
              <label key={field.key} className={styles.fact}>
                <span className={styles.factLabel}>{field.label}</span>
                <Cell field={field} value={values[field.key] as Scalar} onChange={(value) => set(section.key, field.key, value)} />
              </label>
            ))}
            {section.fields
              .filter((field) => field.type === "list")
              .map((field) => (
                <Rows
                  key={field.key}
                  field={field}
                  rows={Array.isArray(values[field.key]) ? (values[field.key] as StatRow[]) : []}
                  onChange={(rows) => set(section.key, field.key, rows.length > 0 ? rows : undefined)}
                />
              ))}
          </section>
        );
      })}
    </div>
  );
}

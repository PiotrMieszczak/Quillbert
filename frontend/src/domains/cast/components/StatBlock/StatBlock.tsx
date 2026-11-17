import type { Sheet, SheetField, StatRow, Stats, StatValue } from "../../model/types";
import styles from "./StatBlock.module.css";

type Scalar = number | string | undefined;

/** One value of the sheet: text when read, an input of the field's type when edited. */
function Cell({ field, value, onChange }: { field: SheetField; value: Scalar; onChange?: (value: Scalar) => void }) {
  if (!onChange) return <span className={styles.value}>{value ?? "—"}</span>;
  return field.type === "int" ? (
    <input
      className={styles.input}
      type="number"
      step={1}
      min={field.min}
      max={field.max}
      value={value ?? ""}
      aria-label={field.label}
      onChange={(event) => onChange(event.target.value === "" ? undefined : Number(event.target.value))}
    />
  ) : (
    <input
      className={styles.input}
      maxLength={2000}
      value={value ?? ""}
      aria-label={field.label}
      onChange={(event) => onChange(event.target.value || undefined)}
    />
  );
}

/** A repeating field, such as skills with a speciality: one row per entry. */
function Rows({ field, rows, onChange }: { field: SheetField; rows: StatRow[]; onChange?: (rows: StatRow[]) => void }) {
  const columns = field.itemFields ?? [];
  const setCell = (index: number, key: string, value: Scalar) =>
    onChange?.(
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
                <th key={column.key} scope="col">
                  {column.label}
                </th>
              ))}
              {onChange && <td />}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              // Rows have no identity of their own; the index is stable while one is edited.
              <tr key={index}>
                {columns.map((column) => (
                  <td key={column.key}>
                    <Cell
                      field={column}
                      value={row[column.key]}
                      onChange={onChange && ((value) => setCell(index, column.key, value))}
                    />
                  </td>
                ))}
                {onChange && (
                  <td>
                    <button
                      type="button"
                      className={styles.remove}
                      aria-label={`Remove ${field.label} row ${index + 1}`}
                      onClick={() => onChange(rows.filter((_, at) => at !== index))}
                    >
                      ×
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {rows.length === 0 && !onChange && <p className={styles.none}>None yet.</p>}
      {onChange && (
        <button type="button" className={styles.addRow} onClick={() => onChange([...rows, {}])}>
          Add {field.label.toLowerCase()}
        </button>
      )}
    </div>
  );
}

type StatBlockProps = {
  sheet: Sheet;
  stats: Stats;
  /** Present while editing; without it the block is read-only. */
  onChange?: (stats: Stats) => void;
};

/** The stat block of a character, laid out by the campaign system's sheet (ADR-0030). */
export function StatBlock({ sheet, stats, onChange }: StatBlockProps) {
  const set = (section: string, key: string, value: StatValue | undefined) => {
    const { [key]: _dropped, ...rest } = stats[section] ?? {};
    onChange?.({ ...stats, [section]: value === undefined ? rest : { ...rest, [key]: value } });
  };
  return (
    <>
      {sheet.sections.map((section) => {
        // Stats saved before the sheet existed can hold any shape here (ADR-0030 NEG-002);
        // what does not fit is shown as empty, never allowed to break the page.
        const saved: unknown = stats[section.key];
        const values = (saved && typeof saved === "object" && !Array.isArray(saved) ? saved : {}) as Stats[string];
        const scalars = section.fields.filter((field) => field.type !== "list");
        return (
          <section key={section.key} className={styles.section} aria-label={section.label}>
            <h3 className={styles.heading}>{section.label}</h3>
            {scalars.length > 0 && (
              <div className={styles.tiles}>
                {scalars.map((field) => (
                  <div key={field.key} className={styles.tile}>
                    <span className={styles.key}>{field.label}</span>
                    <Cell
                      field={field}
                      value={values[field.key] as Scalar}
                      onChange={onChange && ((value) => set(section.key, field.key, value))}
                    />
                  </div>
                ))}
              </div>
            )}
            {section.fields
              .filter((field) => field.type === "list")
              .map((field) => (
                <Rows
                  key={field.key}
                  field={field}
                  rows={Array.isArray(values[field.key]) ? (values[field.key] as StatRow[]) : []}
                  onChange={onChange && ((rows) => set(section.key, field.key, rows.length > 0 ? rows : undefined))}
                />
              ))}
          </section>
        );
      })}
    </>
  );
}

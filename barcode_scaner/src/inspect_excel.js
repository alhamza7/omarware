const { EXCEL_PATH } = require("./config");
const ExcelJS = require("exceljs");

async function main() {
  const wb = new ExcelJS.Workbook();
  await wb.xlsx.readFile(EXCEL_PATH);
  const ws = wb.worksheets[0];
  console.log("Worksheet:", ws && ws.name);
  for (let r = 1; r <= 8; r++) {
    const row = ws.getRow(r).values.slice(1);
    console.log(`Row ${r}:`, row);
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});













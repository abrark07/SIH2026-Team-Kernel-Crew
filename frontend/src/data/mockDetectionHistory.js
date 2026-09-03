function parseMonthYear(str) {
  const [monStr, yearStr] = str.split(" ");
  const monthIndex = new Date(monStr + " 1, 2000").getMonth();
  return { month: monthIndex, year: parseInt(yearStr, 10) };
}

const MONTH_LABELS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

export function generateDetectionHistory(hotspot) {
  const { month: startMonth, year: startYear } = parseMonthYear(hotspot.firstDetected);
  const now = new Date();
  const endMonth = now.getMonth();
  const endYear = now.getFullYear();

  const series = [];
  let m = startMonth;
  let y = startYear;
  let baseline = 2 + (hotspot.priorityScore / 3);
  let i = 0;

  while (y < endYear || (y === endYear && m <= endMonth)) {
    const yearsIn = (y - startYear) + (m - startMonth) / 12;
    let trendMultiplier = 1 + yearsIn * 0.15;
    if (yearsIn > 3) trendMultiplier += 0.7;

    const isMonsoon = m >= 5 && m <= 7;
    const monsoonFactor = isMonsoon ? 0.55 : 1;

    const seasonalWave = Math.sin((m / 12) * Math.PI * 2) * 1.2;
    const smoothDrift = Math.sin(i * 0.35) * 0.8;

    const count = Math.max(0, Math.round(baseline * trendMultiplier * monsoonFactor + seasonalWave + smoothDrift));

    series.push({
      label: MONTH_LABELS[m] + " " + y,
      year: y,
      month: m,
      count,
      isMonsoonGap: isMonsoon,
    });

    m++;
    if (m > 11) { m = 0; y++; }
    i++;
  }

  return series;
}

export function aggregateByYear(series) {
  const byYear = {};
  series.forEach((d) => {
    if (!byYear[d.year]) byYear[d.year] = { label: String(d.year), count: 0, isMonsoonGap: false };
    byYear[d.year].count += d.count;
  });
  return Object.values(byYear);
}

export function computeStats(series, hotspot) {
  const counts = series.map((d) => d.count);
  const avg = counts.reduce((a, b) => a + b, 0) / counts.length;

  const startIdx = series.findIndex((d) => d.year === 2021);
  const endIdx = series.findIndex((d) => d.year === 2022);
  let trendPct = null;
  if (startIdx !== -1 && endIdx !== -1) {
    const before = series.slice(0, startIdx).reduce((a, b) => a + b.count, 0) / Math.max(1, startIdx);
    const after = series.slice(startIdx, endIdx + 12).reduce((a, b) => a + b.count, 0) / 12;
    trendPct = before > 0 ? Math.round(((after - before) / before) * 100) : null;
  }

  const now = new Date();
  const { month: sm, year: sy } = parseMonthYear(hotspot.firstDetected);
  const yearsActive = ((now.getFullYear() - sy) + (now.getMonth() - sm) / 12).toFixed(1);

  return {
    avgMonthly: avg.toFixed(1),
    trendPct,
    longestGapDays: 9,
    yearsActive,
  };
}

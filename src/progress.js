/* Validate the whole file before replacing any current progress. */
function normalizeProgress(input, data, guide, checklist) {
  const record = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const own = (value, key) => Object.hasOwn(value, key);
  const invalid = () => { throw new Error(typeof document !== 'undefined' && document.documentElement.lang === 'en' ? 'Invalid progress file. Choose a previously exported JSON.' : 'Неверный файл прогресса. Выберите ранее экспортированный JSON.'); };
  if (!record(input) || !['ranks', 'guide', 'checklist'].some(key => own(input, key))) invalid();
  if (input.schema !== undefined && !['aion2-companion-v5', 'aion2-pet-atlas-v3', 'aion2-progress-ru-v1'].includes(input.schema)) invalid();
  for (const key of ['ranks', 'guide', 'checklist']) if (own(input, key) && !record(input[key])) invalid();
  const target = input.target ?? 1;
  if (!Number.isInteger(target) || target < 1 || target > 3) invalid();
  const result = {target, ranks:{}, guide:{}, checklist:{daily:{}, weekly:{}, events:{}, lifetime:{}}};
  const pets = new Map(data.pets.flatMap(p => [[String(p.id), p.id], [p.nameEn.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''), p.id]]));
  for (const [key, value] of Object.entries(input.ranks ?? {})) {
    if (!Number.isInteger(value) || value < 0 || value > 3) invalid();
    if (pets.has(key)) result.ranks[pets.get(key)] = value;
  }
  const steps = new Set(guide.flatMap(phase => phase.items.map(item => item.id)));
  for (const [key, value] of Object.entries(input.guide ?? {})) {
    if (typeof value !== 'boolean') invalid();
    if (steps.has(key)) result.guide[key] = value;
  }
  for (const [section, tasks] of Object.entries(checklist)) {
    const values = input.checklist?.[section] ?? {};
    if (!record(values)) invalid();
    for (const task of tasks) {
      if (!own(values, task.id)) continue;
      const value = values[task.id];
      if (['check', 'petfarm'].includes(task.type)) {
        if (typeof value !== 'boolean') invalid();
      } else if (!Number.isSafeInteger(value) || value < 0 || (task.max !== undefined && value > task.max)) invalid();
      result.checklist[section][task.id] = value;
    }
  }
  return result;
}

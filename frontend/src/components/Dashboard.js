import React, {useMemo} from 'react';
export default function Dashboard({statuses}){
  const summary = useMemo(()=>{
    const total = statuses.length;
    const paid = statuses.filter(s=>s.paid).length;
    const yellow = statuses.filter(s=>s.color==='yellow').length;
    const red = statuses.filter(s=>s.color==='red').length;
    return {total, paid, yellow, red};
  }, [statuses]);
  return (<div className='card'>
    <h2>Monthly Summary</h2>
    <div>Total cards: {summary.total}</div>
    <div>Paid this month: {summary.paid}</div>
    <div>Due soon (≤5 days): {summary.yellow}</div>
    <div>Past due: {summary.red}</div>
  </div>);
}

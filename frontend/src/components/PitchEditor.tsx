import React from "react";

export default function PitchEditor({ initial }: { initial?: string }) {
  const [text, setText] = React.useState(initial || "");
  return (
    <div className="p-4 border rounded-lg bg-white">
      <textarea value={text} onChange={e => setText(e.target.value)} className="textarea textarea-bordered w-full h-64" />
      <div className="flex gap-2 mt-2">
        <button className="btn btn-primary">Save</button>
        <button className="btn">Export PDF</button>
      </div>
    </div>
  );
}
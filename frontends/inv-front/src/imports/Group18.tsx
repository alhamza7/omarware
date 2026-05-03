import svgPaths from "./svg-1fheb9k1ht";

function Group() {
  return (
    <div className="absolute left-[6.7px] size-[120.6px] top-[6.7px]">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 120.6 120.6">
        <g id="Group 8">
          <g id="Ellipse" />
          <g id="Ellipse_2">
            <mask fill="white" id="path-1-inside-1_9_282">
              <path d={svgPaths.pcc64cc0} />
            </mask>
            <path d={svgPaths.pcc64cc0} fill="var(--fill-0, white)" mask="url(#path-1-inside-1_9_282)" stroke="var(--stroke-0, #151515)" strokeWidth="12" />
          </g>
          <g id="Ellipse_3">
            <mask fill="white" id="path-2-inside-2_9_282">
              <path d={svgPaths.p3db2a280} />
            </mask>
            <path d={svgPaths.p3db2a280} fill="var(--fill-0, #E11B1D)" mask="url(#path-2-inside-2_9_282)" stroke="var(--stroke-0, #151515)" strokeWidth="12" />
          </g>
          <circle cx="60.3" cy="60.3" fill="var(--fill-0, #D0D0D0)" id="Ellipse_4" r="17.1" stroke="var(--stroke-0, #151515)" strokeWidth="6" />
        </g>
      </svg>
    </div>
  );
}

function Toggle() {
  return (
    <div className="absolute contents left-0 top-0" data-name="toggle">
      <div className="absolute bg-[#ebebeb] h-[134px] left-0 rounded-[200px] top-0 w-[268px]" data-name="bg" />
      <Group />
    </div>
  );
}

export default function Group1() {
  return (
    <div className="relative size-full">
      <Toggle />
    </div>
  );
}
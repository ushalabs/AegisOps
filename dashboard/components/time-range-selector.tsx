"use client";

import {
  useState,
} from "react";

import {
  useRouter,
} from "next/navigation";

import {
  Check,
  ChevronDown,
  Clock3,
} from "lucide-react";


export type TimeRange =
  | "1h"
  | "6h"
  | "24h"
  | "7d";


const options: {
  value: TimeRange;
  label: string;
}[] = [
  {
    value: "1h",
    label: "Last 1 hour",
  },
  {
    value: "6h",
    label: "Last 6 hours",
  },
  {
    value: "24h",
    label: "Last 24 hours",
  },
  {
    value: "7d",
    label: "Last 7 days",
  },
];


export default function TimeRangeSelector({
  value,
}: {
  value: TimeRange;
}) {
  const router =
    useRouter();

  const [
    open,
    setOpen,
  ] = useState(false);


  const selected =
    options.find(
      (option) =>
        option.value === value
    ) ?? options[2];


  function selectRange(
    range: TimeRange
  ) {
    setOpen(false);

    if (range === "24h") {
      router.push("/");
      return;
    }

    router.push(
      `/?range=${range}`
    );
  }


  return (
    <div className="relative">

      <button
        type="button"
        onClick={() =>
          setOpen(
            (current) =>
              !current
          )
        }
        className="
          flex items-center gap-3
          rounded-xl
          border border-slate-200
          bg-white
          px-4 py-2.5
          text-sm font-medium
          shadow-sm
          transition
          hover:border-slate-300
          hover:bg-slate-50
        "
      >

        <Clock3
          className="
            h-4 w-4
            text-slate-500
          "
        />

        {selected.label}

        <ChevronDown
          className={[
            "h-4 w-4 text-slate-400 transition",
            open
              ? "rotate-180"
              : "",
          ].join(" ")}
        />

      </button>


      {open && (
        <div
          className="
            absolute
            right-0
            z-50
            mt-2
            w-44
            overflow-hidden
            rounded-xl
            border
            border-slate-200
            bg-white
            p-1.5
            shadow-xl
          "
        >

          {options.map(
            (option) => (
              <button
                key={
                  option.value
                }
                type="button"
                onClick={() =>
                  selectRange(
                    option.value
                  )
                }
                className="
                  flex w-full
                  items-center
                  justify-between
                  rounded-lg
                  px-3 py-2.5
                  text-left
                  text-sm
                  text-slate-700
                  transition
                  hover:bg-slate-50
                "
              >

                {
                  option.label
                }

                {
                  option.value ===
                    value && (
                    <Check
                      className="
                        h-4 w-4
                        text-blue-600
                      "
                    />
                  )
                }

              </button>
            )
          )}

        </div>
      )}

    </div>
  );
}
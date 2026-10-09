import Link from "next/link";

import {
  BookOpen,
  ChevronRight,
} from "lucide-react";

import {
  getDashboardPostmortems,
} from "@/lib/aegisops";


export const instant = false;


export default async function PostmortemsPage() {
  const postmortems =
    await getDashboardPostmortems(
      100
    );


  return (
    <main className="p-6 xl:p-8">

      <div className="mx-auto max-w-[1700px]">

        <div className="mb-6">

          <h1
            className="
              text-3xl
              font-bold
              tracking-tight
            "
          >
            Postmortems
          </h1>

          <p
            className="
              mt-1
              text-sm
              text-slate-600
            "
          >
            Resolved incident analysis and reusable incident memory.
          </p>

        </div>


        <section
          className="
            grid
            gap-4
            xl:grid-cols-2
          "
        >

          {postmortems.map(
            (postmortem) => (

              <Link
                key={
                  postmortem.id
                }
                href={
                  `/postmortems/${postmortem.incident_id}`
                }
                className="
                  group
                  rounded-[26px]
                  border
                  border-white/35
                  p-5
                  transition
                  hover:-translate-y-0.5
                  hover:bg-white/28
                "
                style={{
                  background:
                    "rgba(255,255,255,.22)",

                  backdropFilter:
                    "blur(20px)",
                }}
              >

                <div
                  className="
                    flex
                    items-start
                    justify-between
                    gap-4
                  "
                >

                  <div
                    className="
                      flex
                      min-w-0
                      gap-3
                    "
                  >

                    <div
                      className="
                        flex
                        h-11
                        w-11
                        shrink-0
                        items-center
                        justify-center
                        rounded-2xl
                        bg-violet-100/60
                      "
                    >
                      <BookOpen
                        className="
                          h-5
                          w-5
                          text-violet-600
                        "
                      />
                    </div>


                    <div className="min-w-0">

                      <p
                        className="
                          truncate
                          font-semibold
                          text-slate-950
                        "
                      >
                        {
                          postmortem
                            .incident_title
                        }
                      </p>

                      <p
                        className="
                          mt-1
                          text-xs
                          text-slate-500
                        "
                      >
                        Incident #
                        {
                          postmortem
                            .incident_id
                        }
                        {" · "}
                        {
                          postmortem
                            .incident_service
                        }
                      </p>

                    </div>

                  </div>


                  <ChevronRight
                    className="
                      h-5
                      w-5
                      text-slate-400
                      transition
                      group-hover:translate-x-1
                    "
                  />

                </div>


                <p
                  className="
                    mt-5
                    line-clamp-3
                    text-sm
                    leading-6
                    text-slate-700
                  "
                >
                  {postmortem.summary}
                </p>


                <div
                  className="
                    mt-5
                    rounded-2xl
                    border
                    border-white/25
                    bg-white/13
                    p-4
                  "
                >

                  <p
                    className="
                      text-[10px]
                      font-semibold
                      uppercase
                      tracking-wide
                      text-slate-500
                    "
                  >
                    Root Cause
                  </p>


                  <p
                    className="
                      mt-2
                      line-clamp-2
                      text-sm
                      text-slate-700
                    "
                  >
                    {
                      postmortem.root_cause
                      ?? "Not established."
                    }
                  </p>

                </div>

              </Link>

            )
          )}

        </section>

      </div>

    </main>
  );
}
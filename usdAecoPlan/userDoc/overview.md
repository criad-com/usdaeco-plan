# Overview

usdAecoPlan describes programme records and their relationships to the built
thing. Read the [minimal example](../examples/minimal.usda) for a ceiling
installation and handover, then the [worked use case](../../docs/usecase.md).

![Office corridor programme](usdAecoPlanExample.png)

`AecoProgramme` owns an identity, clock mapping and programme scope.
`AecoActivity` children form the WBS and use the core `members` collection.
`AecoMilestone` is an activity event. Schedule and workspace APIs apply to
activities, including milestones, and refuse geometry and programme roots.

The parallel `aeco:plan:predecessorIds`, `lagDays` and `linkType` arrays retain
every source link row in order, including exact repeats. The unique path-sorted
`predecessors` relationship is a derived convenience in a separate layer.
Dates are ISO-8601 date strings; visibility samples belong only to the derived
4D view. Muting that view leaves the programme and source geometry intact.

The [example outputs](../../examples/datacentre/README.md) include two schedule
issues, two 12-week sequences, Gantt SVGs and a relocatable stock-USD result.

# Data Fields

A comprehensive overview of the data fields scraped from the UFC Stats website.

## Fighter Stats

| Field | Description |
| ----- | ----------- |
| `Name` | The name of the fighter |
| `Wins` | The number of wins the fighter has |
| `Losses` | The number of losses the fighter has |
| `Draws` | The number of draws the fighter has |
| `NC` | The number of no contests the fighter has |
| `Height` | The height of the fighter in inches (in) |
| `Weight` | The weight of the fighter in pounds (lbs) |
| `Reach` | The reach (i.e. wingspan) of the fighter in inches (in) |
| `Stance` | The stance of the fighter (e.g. Orthodox, Southpaw, Switch, etc.) |
| `DOB` | The date of birth of the fighter |
| `SLpM` | The number of significant strikes the fighter lands per minute |
| `Str. Acc.` | The percentage of significant strikes the fighter lands out of those attempted, as a proportion (between 0 and 1) |
| `SApM` | The number of significant strikes the fighter absorbs per minute |
| `Str. Def.` | The percentage of significant strikes the fighter avoids out of those attempted by the opponent, as a proportion (between 0 and 1) |
| `TD Avg.` | The average number of takedowns the fighter lands per 15 minutes |
| `TD Acc.` | The percentage of takedowns the fighter lands out of those attempted, as a proportion (between 0 and 1) |
| `TD Def.` | The percentage of takedowns the fighter avoids out of those attempted by the opponent, as a proportion (between 0 and 1) |
| `Sub. Avg.` | The average number of submissions the fighter attempts per 15 minutes |


It is important to note that all fields besides basic static information (e.g. `Name`, `Height`, `Reach`, `Stance`, `DOB`) are dynamic and change over time. For example, a fighter's `Wins` and `Losses` often change after each fight, or a fighter's `Weight` may change if he or she decides to compete in a different weight class at some point in their career. As such, the data scraped from the UFC Stats website is a snapshot of the fighter's stats **at the time of scraping** and consequently extreme care must be taken during feature engineering to ensure that the data is not leaked into the model. We can however generate historical versions of these fields and other features using the bouts data.


## Bouts Data

To keep the following table short, for the fields that exist for each fighter in a given bout (`R_` and `B_` designate the fighters in the red and blue corners respectively), I will just be explaining the fields for the red corner fighter since the meanings are identical for the blue corner fighter. Also, for round-by-round stats, I will refer to the first round `R1` as an example but the same fields exist for all rounds (e.g. `R2`, `R3`, etc.).

| Field | Description |
| ----- | ----------- |
| `URL` | The URL of the bout on the UFC Stats website, not exactly useful for feature engineering, but it's a nice to have when sanity checking data |
| `Event` | The name of the event the bout took place at |
| `Date` | The date the bout took place |
| `R_Name` | The name of the fighter in the red corner |
| `R_Result` | The result of the fighter in the red corner (e.g. W = Win, L = Loss, D = Draw, NC = No Contest (overturned)) |
| `Bout Type` | A combination of weight class, whether or not it was a title fight, and if it was some kind of special event |
| `Method` | The method of victory (e.g. KO/TKO, Submission, Decision, Overturned, etc.) |
| `Round` | The round the bout ended in |
| `Time` | The time the bout ended at during the above round |
| `Format` | The time format of the bout (number of rounds and time per round) |
| `Total Time` | The total time the bout lasted in minutes |
| `R_KD` | The number of knockdowns scored by the fighter in the red corner |
| `R_Total Str. Landed` | The total number of strikes (not just significant strikes) landed by the fighter in the red corner |
| `R_Total Str. Attempted` | The total number of strikes (not just significant strikes) attempted by the fighter in the red corner |
| `R_TD Landed` | The total number of takedowns landed by the fighter in the red corner |
| `R_TD Attempted` | The total number of takedowns attempted by the fighter in the red corner |
| `R_TD %` | The percentage of takedowns landed by the fighter in the red corner out of those attempted, as a proportion (between 0 and 1) |
| `R_Sub. Att` | The total number of submission attempts by the fighter in the red corner |
| `R_Rev.` | The number of reversals (position reversal when grappling) scored by the fighter in the red corner |
| `R_Ctrl` | The total time the fighter in the red corner spent in control when grappling (i.e. on top of the opponent) in minutes |
| `R_KD_R1` | The number of knockdowns scored by the fighter in the red corner in the first round |
| `R_Total Str. Landed_R1` | The total number of strikes (not just significant strikes) landed by the fighter in the red corner in the first round |
| `R_Total Str. Attempted_R1` | The total number of strikes (not just significant strikes) attempted by the fighter in the red corner in the first round |
| `R_TD Landed_R1` | The total number of takedowns landed by the fighter in the red corner in the first round |
| `R_TD Attempted_R1` | The total number of takedowns attempted by the fighter in the red corner in the first round |
| `R_TD %_R1` | The percentage of takedowns landed by the fighter in the red corner in the first round out of those attempted, as a proportion (between 0 and 1) |
| `R_Sub. Att_R1` | The total number of submission attempts by the fighter in the red corner in the first round |
| `R_Rev._R1` | The number of reversals (position reversal when grappling) scored by the fighter in the red corner in the first round |
| `R_Ctrl_R1` | The total time the fighter in the red corner spent in control when grappling (i.e. on top of the opponent) in the first round in minutes |
| `R_Sig. Str. Landed` | The total number of significant strikes landed by the fighter in the red corner |
| `R_Sig. Str. Attempted` | The total number of significant strikes attempted by the fighter in the red corner |
| `R_Sig. Str. %` | The percentage of significant strikes landed by the fighter in the red corner out of those attempted, as a proportion (between 0 and 1) |
| `R_Head Landed` | The total number of significant strikes landed by the fighter in the red corner to the opponent's head |
| `R_Head Attempted` | The total number of significant strikes attempted by the fighter in the red corner to the opponent's head |
| `R_Body Landed` | The total number of significant strikes landed by the fighter in the red corner to the opponent's body |
| `R_Body Attempted` | The total number of significant strikes attempted by the fighter in the red corner to the opponent's body |
| `R_Leg Landed` | The total number of significant strikes landed by the fighter in the red corner to the opponent's legs |
| `R_Leg Attempted` | The total number of significant strikes attempted by the fighter in the red corner to the opponent's legs |
| `R_Distance Landed` | The total number of significant strikes landed by the fighter in the red corner at a distance |
| `R_Distance Attempted` | The total number of significant strikes attempted by the fighter in the red corner at a distance |
| `R_Clinch Landed` | The total number of significant strikes landed by the fighter in the red corner in the clinch |
| `R_Clinch Attempted` | The total number of significant strikes attempted by the fighter in the red corner in the clinch |
| `R_Ground Landed` | The total number of significant strikes landed by the fighter in the red corner on the ground |
| `R_Ground Attempted` | The total number of significant strikes attempted by the fighter in the red corner on the ground |
| `R_Sig. Str. Landed_R1` | The total number of significant strikes landed by the fighter in the red corner in the first round |
| `R_Sig. Str. Attempted_R1` | The total number of significant strikes attempted by the fighter in the red corner in the first round |
| `R_Sig. Str. %_R1` | The percentage of significant strikes landed by the fighter in the red corner in the first round out of those attempted, as a proportion (between 0 and 1) |
| `R_Head Landed_R1` | The total number of significant strikes landed by the fighter in the red corner to the opponent's head in the first round |
| `R_Head Attempted_R1` | The total number of significant strikes attempted by the fighter in the red corner to the opponent's head in the first round |
| `R_Body Landed_R1` | The total number of significant strikes landed by the fighter in the red corner to the opponent's body in the first round |
| `R_Body Attempted_R1` | The total number of significant strikes attempted by the fighter in the red corner to the opponent's body in the first round |
| `R_Leg Landed_R1` | The total number of significant strikes landed by the fighter in the red corner to the opponent's legs in the first round |
| `R_Leg Attempted_R1` | The total number of significant strikes attempted by the fighter in the red corner to the opponent's legs in the first round |
| `R_Distance Landed_R1` | The total number of significant strikes landed by the fighter in the red corner at a distance in the first round |
| `R_Distance Attempted_R1` | The total number of significant strikes attempted by the fighter in the red corner at a distance in the first round |
| `R_Clinch Landed_R1` | The total number of significant strikes landed by the fighter in the red corner in the clinch in the first round |
| `R_Clinch Attempted_R1` | The total number of significant strikes attempted by the fighter in the red corner in the clinch in the first round |
| `R_Ground Landed_R1` | The total number of significant strikes landed by the fighter in the red corner on the ground in the first round |
| `R_Ground Attempted_R1` | The total number of significant strikes attempted by the fighter in the red corner on the ground in the first round |

As mentioned earlier, this is a truncated version of all the columns. As of the design right now, there are 349 columns in the dataset. Most of this is just from the round-by-round stats, but these could be useful for feature engineering; for instance, looking at the round to round change in striking performance or output could gauge a fighter's stamina and how that changes also from fight to fight throughout a fighter's career.

In a similar way to the fighter data, the bouts data captures information about the overall bout **after it has ended**. So again, one must be careful when creating predictors to not include information that would not be known before the bout has ended. Furthermore, data needs to be split when doing train/test or cross validation in such a way that respects time to avoid data leakage.

Lastly, the data includes stats on fights outside of regular UFC events (e.g. The Ultimate Fighter, Dana White's Contender Series, etc.) as well as from other promotions. These stats can be used to build up the historical features of a fighter, but should not be used in training/testing data for a model that is trying to predict UFC fights. In fact, it may be that ignoring stats from these fights when creating those features is better because different promotions have different levels of competition—this should be explored. Also, we should omit any fights occurring before March 21, 2010 when creating our train/test data since all records before this defaulted to the winner as the red corner fighter (and therefore imbalancing the data). It might even be better to make this cutoff date even more recent since the UFC has evolved a lot over the years—again, this should be explored, but March 21, 2010 is the furthest back we should consider for train/test data. We can however use all the data for feature engineering.
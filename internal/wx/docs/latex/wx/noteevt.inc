\wxheading{Event handling}

To process input from a notebook control, use the following event handler macros to direct input to member
functions that take a \helpref{wxNotebookEvent}{wxnotebookevent} argument.

\twocolwidtha{7cm}
\begin{twocollist}\itemsep=0pt
\twocolitem{{\bf EVT\_NOTEBOOK\_PAGE\_CHANGED(id, func)}}{The page selection was changed. Processes a
wxEVT\_COMMAND\_NOTEBOOK\_PAGE\_CHANGED event.}
\twocolitem{{\bf EVT\_NOTEBOOK\_PAGE\_CHANGING(id, func)}}{The page selection is about to be changed.
Processes a wxEVT\_COMMAND\_NOTEBOOK\_PAGE\_CHANGING event. This event can be \helpref{vetoed}{wxnotifyeventveto}.}
\end{twocollist}


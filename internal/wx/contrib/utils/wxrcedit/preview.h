/////////////////////////////////////////////////////////////////////////////
// Purpose:     XML resources editor
// Author:      Vaclav Slavik
// Created:     2000/05/05
// RCS-ID:      $Id$
// Copyright:   (c) 2000 Vaclav Slavik
// Licence:     wxWindows licence
/////////////////////////////////////////////////////////////////////////////

#if defined(__GNUG__) && !defined(__APPLE__)
    #pragma interface "preview.h"
#endif

#ifndef _PREVIEW_H_
#define _PREVIEW_H_



class WXDLLEXPORT wxXmlNode;
class WXDLLEXPORT wxScrolledWindow;
class WXDLLEXPORT wxTextCtrl;
class WXDLLEXPORT wxSplitterWindow;
class WXDLLEXPORT wxXmlResource;
class WXDLLEXPORT wxXmlDocument;
#include "wx/frame.h"


class PreviewFrame : public wxFrame
{
    public:
        PreviewFrame();
        ~PreviewFrame();

        void Preview(wxXmlNode *node,wxXmlDocument *doc);
        void MakeDirty();
                // current node updated, needs preview refresh
                // (will be done once mouse enters preview win)

        static PreviewFrame *Get();
        void ResetResource();

    private:
        void PreviewMenu();
        void PreviewToolbar();
        void PreviewPanel();
        void PreviewWXFrame();

    private:
        static PreviewFrame *ms_Instance;
        wxXmlNode *m_Node;
        wxXmlDocument *m_Doc;
        wxScrolledWindow *m_ScrollWin;
#if wxUSE_LOG
        wxTextCtrl *m_LogCtrl;
#endif // wxUSE_LOG
        wxSplitterWindow *m_Splitter;

        wxXmlResource *m_RC;
        wxString m_TmpFile;

        bool m_Dirty;

        DECLARE_EVENT_TABLE()
        void OnMouseEnter(wxMouseEvent& event);
};


#endif

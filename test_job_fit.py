import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
import db
from job_fit import score_job, rank_jobs, load_profile
from proposal_generator import draft_proposal

class FitTests(unittest.TestCase):
    def test_niche_match_and_finance_without_video(self):
        video = score_job({'title':'Crypto short-form video editor','snippet':'TikTok vertical 9:16 captions and chart animations. '*5,'budget':'$100'})
        research = score_job({'title':'Crypto financial researcher','snippet':'Write market research every day.'})
        self.assertGreaterEqual(video['score'], 65)
        self.assertLessEqual(research['score'], 30)
        self.assertIsNone(research['track'])

    def test_manufacturing_workflow_is_not_software_automation(self):
        for title, snippet in [('Industrial Sheet Metal Enclosure Design Engineer', 'Industrial automation equipment needs mechanical CAD engineer.'), ('Convert SolidWorks Files to NC1', 'Manufacturing workflow conversion of SolidWorks files.')]:
            result = score_job({'title':title,'snippet':snippet,'budget':'Hourly: $30'})
            self.assertIsNone(result['track'])
            self.assertLessEqual(result['score'], 30)

    def test_short_clips_do_not_imply_vertical_short_form(self):
        result=score_job({'title':'Football compilation video', 'snippet':'Make a five minute compilation from a library of short football clips.'})
        self.assertFalse(any('Đúng định dạng' in s for s in result['reasons']))

    def test_truncated_email_has_limited_confidence(self):
        result=score_job({'title':'Short-form video editor', 'snippet':'We need short-form video editing… Payment verified '+('x'*200)})
        self.assertEqual(result['confidence'],'limited')
        self.assertTrue(any('bị cắt' in s for s in result['gaps']))
        self.assertFalse(any('đủ dài' in s for s in result['reasons']))

    def test_low_fixed_budget_and_view_based_compensation(self):
        base={'title':'Short-form video editor','snippet':'YouTube Shorts for a brand.'*10,'budget':'Fixed: $200.00'}
        cheap=dict(base,budget='Fixed: $10.00')
        self.assertLess(score_job(cheap)['score'],score_job(base)['score'])
        views=dict(base,title='Content clipper $2.50 per 1,000 views')
        self.assertTrue(any('lượt xem' in flag for flag in score_job(views)['flags']))

    def test_capcut_project_is_not_claimed_as_remotion_capability(self):
        fit=score_job({'title':'CapCut video editor','snippet':'Restyle a reel already cut in CapCut.'},dict(load_profile(),editing_tools=[]))
        self.assertTrue(any('phần mềm' in gap.lower() for gap in fit['gaps']))

    def test_risks_and_unverified_requirements_reduce_priority(self):
        base={'title':'Short video editor','snippet':'Reels vertical editing. '*10,'budget':'$100'}
        risky=dict(base,snippet=base['snippet']+' Must deliver Premiere source files, 3D animation, unlimited revisions, unpaid test.')
        self.assertLess(score_job(risky)['score'],score_job(base)['score'])
        self.assertTrue(score_job(risky)['flags'])
        self.assertGreaterEqual(len(score_job(risky)['gaps']),2)

    def test_automation_and_nonjob_exclusion(self):
        job={'id':1,'email_type':'job_alert','title':'Python automation with Telegram webhook','snippet':'Map form data to SQLite database. '*8,'budget':'$150'}
        profile=dict(load_profile(),tracks=['automation'])
        self.assertEqual(score_job(job,profile)['track'],'automation')
        self.assertEqual(len(rank_jobs([job,dict(job,id=2,email_type='message')],5,profile)),1)

    def test_video_focus_excludes_other_service_tracks(self):
        profile=dict(load_profile(),tracks=['short_video'])
        jobs=[{'id':1,'email_type':'job_alert','title':'Python Telegram automation','snippet':'Build a form workflow.'},{'id':2,'email_type':'job_alert','title':'TikTok video editor','snippet':'Edit a vertical reel.'},{'id':3,'email_type':'job_alert','title':'Mechanical CAD engineer','snippet':'Industrial automation enclosure.'}]
        ranked=rank_jobs(jobs,5,profile)
        self.assertEqual([item['job']['id'] for item in ranked],[2])

    def test_confirmed_davinci_capcut_workflow(self):
        profile=dict(load_profile(),editing_tools=['DaVinci Resolve Free','CapCut'])
        for title in ('CapCut video editor','DaVinci Resolve video editor'):
            fit=score_job({'title':title,'snippet':'Edit a vertical reel from supplied footage.'},profile)
            self.assertFalse(any('Phần mềm biên tập' in gap for gap in fit['gaps']))
        studio=score_job({'title':'DaVinci Resolve video editor','snippet':'Magic Mask required.'},profile)
        self.assertTrue(any('Studio' in gap for gap in studio['gaps']))

    def test_drafts_have_no_fabricated_claims(self):
        for title in ['Translate Vietnamese','Crypto reels editor','Python automation']:
            text=draft_proposal({'title':title,'snippet':'Unlimited revisions and free test requested'})
            for claim in ['70%', '183K', 'native Vietnamese','extensive experience','24-48h','unlimited revisions','free 15']:
                self.assertNotIn(claim,text)
            self.assertIn('paid milestone',text)
            self.assertIn('before agreeing',text)

    def test_recent_db_selection_bounded_and_read_only(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(db,'DB_PATH',str(Path(directory)/'jobs.db')):
            db.init_db()
            db.save_job(1,'upwork','job_alert','other_video','Test','','','','Snippet',False)
            self.assertEqual(len(db.get_recent_jobs(7,1)),1)
            self.assertEqual(db.get_job(1)['title'],'Test')

    def test_telegram_html_escapes_untrusted_snippet(self):
        import telegram_notifier as notifier
        response=Mock(status_code=200)
        response.json.return_value={'ok':True}
        with patch.object(notifier,'TELEGRAM_BOT_TOKEN','test'),patch.object(notifier,'TELEGRAM_CHAT_ID','test'),patch.object(notifier.requests,'post',return_value=response) as send:
            self.assertTrue(notifier.send_telegram_alert('test','test','job_alert',title='Short video',snippet='<script>x</script> & text'))
            text=send.call_args.kwargs['json']['text']
            self.assertIn('&lt;script&gt;',text)
            self.assertNotIn('<script>',text)
            self.assertIn('Độ phù hợp:',text)
            self.assertNotIn('183K',text)

    def test_commands_use_requested_job(self):
        import bot_listener as bot
        job={'id':12,'title':'Video reels','snippet':'vertical video','budget':''}
        with patch.object(bot,'send_reply') as reply,patch.object(bot.db,'get_job',return_value=job) as lookup:
            bot.handle_command('/fit 12')
            lookup.assert_called_once_with(12)
            self.assertIn('12',reply.call_args.args[0])
            lookup.reset_mock()
            bot.handle_command('/draft typo')
            lookup.assert_not_called()
        with patch.object(bot,'send_reply') as reply,patch.object(bot.db,'get_recent_jobs',return_value=[dict(job,email_type='job_alert')]):
            bot.handle_command('/top')
            self.assertIn('/fit 12',reply.call_args.args[0])

    def test_missing_callback_never_selects_latest_job(self):
        import bot_listener as bot
        with patch.object(bot,'TELEGRAM_CHAT_ID','123'),patch.object(bot.requests,'post'),patch.object(bot,'send_reply'),patch.object(bot.db,'get_job_by_uid',return_value={}),patch.object(bot.db,'get_job') as latest:
            bot.handle_callback_query({'id':'x','from':{'id':123},'data':'draft:999'})
            latest.assert_not_called()

if __name__=='__main__':
    unittest.main()

"""Explicit expired security-record cleanup, not placement-history erasure."""
import argparse
import json
from datetime import datetime,timedelta,timezone
from sqlalchemy import delete,func,select
from database import tenant_session
from models import AuthLimit,PasswordResetToken,EmailVerificationToken
def cleanup(college,apply=False):
    cutoff=datetime.now(timezone.utc)-timedelta(days=7);result={}
    with tenant_session(college) as session:
        for model,field in ((AuthLimit,AuthLimit.window_start),(PasswordResetToken,PasswordResetToken.expires_at),(EmailVerificationToken,EmailVerificationToken.expires_at)):
            where=(model.college_id==college,field<cutoff)
            result[model.__tablename__]=session.scalar(select(func.count()).select_from(model).where(*where))
            if apply: session.execute(delete(model).where(*where))
    return {'college_id':college,'applied':apply,'eligible_expired_records':result}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--college',type=int,required=True)
    parser.add_argument('--apply',action='store_true');parser.add_argument('--confirm-expired-security-records',action='store_true')
    args=parser.parse_args()
    if args.college<1 or (args.apply and not args.confirm_expired_security_records): parser.error('Valid tenant and explicit cleanup confirmation required.')
    print(json.dumps(cleanup(args.college,args.apply),indent=2))

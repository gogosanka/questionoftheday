from smh import db
from smh.models.models import *
from datetime import datetime
import os
from smh import app
now = datetime.utcnow()

try:
	if User.query.filter_by(nickname="admin").first() != None:
		app.run(debug=True, threaded=True, port=5000)
	else:
		u = User(nickname="admin", password="shinobi1", created=now)
		q = Question(body="No further Questions.", timestamp=now, author=u)
		qotd = QOTD(qotd=1)
		db.session.add(q)
		db.session.add(qotd)
		db.session.add(u)
		db.session.commit()
		app.run(debug=True, threaded=True, port=5000)
except:
	pass
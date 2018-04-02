from sqlalchemy.orm.exc import NoResultFound
import tempfile, subprocess, string, random, os

# http://skien.cc/blog/2014/01/15/sqlalchemy-and-race-conditions-implementing/
def get_one_or_create(session,
                      model,
                      create_method='',
                      create_method_kwargs=None,
                      **kwargs):
    try:
        return session.query(model).filter_by(**kwargs).one(), True
    except NoResultFound:
        kwargs.update(create_method_kwargs or {})
        created = getattr(model, create_method, model)(**kwargs)
        try:
            session.add(created)
            session.commit()
            return created, False
        except IntegrityError:
            session.rollback()
            return session.query(model).filter_by(**kwargs).one(), True

def gen_ssh_key_pair():
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    filename = '/tmp/' + ''.join(random.SystemRandom().choice(chars) for _ in range(8))

    ret = subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "4096", "-N", "", "-f", filename],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    if ret.returncode != 0:
        return None

    with open(filename, 'r') as priv_file:
        priv_key = priv_file.read()
    os.remove(filename)

    with open(filename + '.pub', 'r') as pub_file:
        pub_key = pub_file.read()
    os.remove(filename + '.pub')

    return (pub_key, priv_key)

SAVE_MODELS = [ 'shinymud.models.area.Area',
                'shinymud.models.user.User']

class ShinyModel(object):
    
    # A dictionary of names of attributes to be saved, and their default values.
    # in the format {attribute_name: [defaultvalue, type]}
    save_attrs = {}
    # a list of names of attributes that allow us to reference a unique instance of this model.
    UNIQUE = []
    
    def __init__(self, **args):
        """Initialize saveable data, and other attributes by keyword args.
        
        if you overwrite this, you should either 
        1) call the super class' init function
        2) understand that you are in charge of handling ALL of the initializing, and plan appropriately.
        """
        self.__changed = True # this instances has been modified, or has not been saved.
        for key, val in args.items():
            setattr(self, key, val)
        for attr in [_ for _ in self.save_attrs if _ not in args]:
            setattr(self, attr, self.save_attrs[attr][0])
    
    def __setattr__(self, key, val):
        if key in self.save_attrs:
            self.__changed = True
        self.__dict__[key] = val
    
    def __ischanged(self):
        try:
            return self.__changed
        except:
            return False
    
    def __exists(self):
        try:
            return bool(self.__dbid)
        except:
            return False
        
    def __get_table_name(self):
        return getattr(self, 'table_name', self.__class__.__name__.lower())
    
    def load(self, conn, **criteria):
        # Try to load from cache.
        # if not in cache, load from db
        cursor = conn.cursor()
        table_name = self.__get_table_name()
        cols = self.save_attrs.keys()
        if not criteria:
            if not self.__exists():
                raise Exception('Cannot execute load without criteria')
            criteria = {'dbid':self.__dbid}
        where_clause = " AND ".join([key + "='" + val + "'" for key,val in criteria.items()])
        cursor.execute('SELECT * FROM %s WHERE %s LIMIT 1' % (table_name, where_clause))
        row = cursor.fetchone()
        if row:
            for i in range(len(row)):
                col_name = cursor.description[i][0]
                if col_name == 'dbid':
                    self.__dbid = row[i]
                else:
                    setattr(self, col_name, self.save_attrs[col_name][1](row[i]))
            self.__changed = False
        # if loaded from db, add to cache
    
    def save(self, conn):
        if self.__ischanged():
            cols = self.save_attrs.keys()
            cursor = conn.cursor()
            table_name = self.__get_table_name()
            if self.__exists():
                # update
                set_values = []
                for key in cols:
                    set_values.append(key + "='" + str(getattr(self, key)) + "'")
                where_clause = "dbid=" + str(self.__dbid)
                cursor.execute("UPDATE %s SET %s WHERE %s" % (table_name, ", ".join(set_values).replace("'", '"'), where_clause))
                conn.commit()
            else:
                # insert
                data = []
                for key in cols:
                    data.append(str(getattr(self, key)))
                print "TEST"
                print table_name
                print ",".join(cols)
                print ",".join(["'" + str(_) + "'" for _ in data])
                cursor.execute("INSERT INTO %s (%s) VALUES (%s)" % (table_name, ",".join(cols) , ",".join(["'" + str(_).replace("'", '"') + "'" for _ in data])))
                self.__dbid = cursor.lastrowid
                conn.commit()
                
    
    def delete(self, conn):
        if self.id:
            cursor = conn.cursor()
            table_name = self.__get_table_name()
            cursor.execute('DELETE FROM ? WHERE dbid=?', (table_name, self.__dbid))
            conn.commit()
            
    

-- 1
select *
from Project p
where not exists
(select *
from WorkedOn w
where p.pid = w.pid
and w.year = 2019);

-- 2
select a.rid, a.name, count(distinct t2.rid)
from Researcher a
left outer join WorkedOn t on a.rid = t.rid
left outer join WorkedOn t2 on t.pid = t2.pid and t2.rid<>a.rid
group by a.rid, a.name;

-- 3
-- returns all in case of ties
with projectspan as
(select w.pid, max(w.year)-min(w.year) as span
from workedon w
group by w.pid)
select p.pid, p.title
from project p, projectspan x
where p.pid = x.pid and x.span = (select min(span) from projectspan);

--Alternative that returns a single project in case of ties
select p.pid, p.title
from project p, (select w.pid, max(w.year)-min(w.year) as span
                from workedon w
                group by w.pid
                order by span asc) x
where p.pid = x.pid 
limit 1;



-- 4
CREATE VIEW rewards AS
        (SELECT p.name, i.total
         FROM   Customer p, Points i
         WHERE  p.cid = i.cid AND i.total > 40);
GRANT SELECT ON rewards TO loyaltydirector;


create table Researcher(rid int primary key, name text, affiliation text);
create table Project(pid int primary key, title text);
create table WorkedOn(rid int references Researcher, pid int references Project, year int);
    
insert into Researcher values(1, 'Alice', 'UMass');
insert into Researcher values(2, 'Bob', 'UMass');
insert into Researcher values(3, 'Carol', 'MIT');
insert into Researcher values(4, 'David', 'CMU');
insert into Researcher values(5, 'Eve', 'CMU');
insert into Project values(345, 'Databases');
insert into Project values(101, 'Chemistry');
insert into Project values(102, 'XX');
insert into Project values(103, 'YY');
insert into WorkedOn values(1, 345, 2010);
insert into WorkedOn values(2, 345, 2019);
insert into WorkedOn values(4, 345, 2008);
insert into WorkedOn values(2, 101, 2008);
insert into WorkedOn values(4, 101, 2018);
insert into WorkedOn values(5, 101, 2019);
insert into WorkedOn values(1, 345, 2011);
insert into WorkedOn values(4, 345, 2011);
insert into WorkedOn values(1, 102, 2010);
insert into WorkedOn values(2, 102, 2018);
insert into WorkedOn values(4, 102, 2000);
insert into WorkedOn values(1, 103, 2015);
insert into WorkedOn values(2, 103, 2018);
    
    


CREATE TABLE Customer (cid INT PRIMARY KEY,
                        name VARCHAR(20));
                    
CREATE TABLE Points (cid INT PRIMARY KEY,
                      total INT,
                      FOREIGN KEY (cid) REFERENCES Customer);
                  
insert into Customer values (1, 'Alpha');
insert into Customer values (2, 'Beta');
insert into Customer values (3, 'Charlie');
insert into Customer values (4, 'Delta');
insert into Customer values (5, 'Echo');


insert into Points values (1, 55);
insert into Points values (2, 12);
insert into Points values (4, 67);
insert into Points values (5, 45);    


CREATE ROLE loyaltydirector;


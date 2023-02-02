from datetime import date

from peewee import CharField, DateField, ForeignKeyField, IntegerField, fn

from juniorguru.models.base import BaseModel
from juniorguru.models.club import ClubUser


class Partner(BaseModel):
    name = CharField()
    slug = CharField(unique=True)
    url = CharField()
    coupon = CharField(null=True, index=True)
    student_coupon = CharField(null=True, index=True)
    logo_path = CharField(null=True)
    poster_path = CharField(null=True)
    role_id = IntegerField(null=True)
    student_role_id = IntegerField(null=True)

    @property
    def list_members(self):
        if not self.coupon:
            return []
        return ClubUser.select() \
            .join(self.__class__, on=(ClubUser.coupon == self.__class__.coupon)) \
            .where((ClubUser.is_member == True) & (ClubUser.coupon == self.coupon))

    @property
    def list_student_members(self):
        if not self.student_coupon:
            return []
        return ClubUser.select() \
            .join(self.__class__, on=(ClubUser.coupon == self.__class__.student_coupon)) \
            .where((ClubUser.is_member == True) & (ClubUser.coupon == self.student_coupon))

    @property
    def list_student_subscriptions_billable(self):
        return self.list_student_subscriptions \
            .where(PartnerStudentSubscription.invoiced_on.is_null())

    def active_partnership(self, today=None):
        today = today or date.today()
        return self.list_partnerships \
            .where(Partnership.starts_on <= today,
                   (Partnership.expires_on >= today) | Partnership.expires_on.is_null()) \
            .order_by(Partnership.starts_on.desc()) \
            .first()

    @classmethod
    def get_by_slug(cls, slug):
        return cls.select() \
            .where(cls.slug == slug) \
            .get()

    @classmethod
    def active_listing(cls, today=None, include_barters=True):
        today = today or date.today()
        expires_after_today = Partnership.expires_on >= today
        if include_barters:
            expires_after_today = (expires_after_today | Partnership.expires_on.is_null())
        return cls.select() \
            .join(Partnership) \
            .join(PartnershipPlan) \
            .group_by(cls) \
            .having(Partnership.starts_on == fn.max(Partnership.starts_on),
                    Partnership.starts_on <= today,
                    expires_after_today) \
            .order_by(PartnershipPlan.hierarchy_rank.desc(), cls.name)

    @classmethod
    def expired_listing(cls, today=None):
        today = today or date.today()
        return cls \
            .select() \
            .join(Partnership) \
            .group_by(cls) \
            .having(Partnership.starts_on == fn.max(Partnership.starts_on),
                    Partnership.starts_on < today,
                    Partnership.expires_on.is_null(False),
                    Partnership.expires_on < today) \
            .order_by(cls.name)

    @classmethod
    def handbook_listing(cls, today=None):
        today = today or date.today()
        return cls.active_listing() \
            .join(PartnershipBenefit) \
            .where(PartnershipBenefit.slug == 'logo_handbook') \
            .order_by(cls.name)

    @classmethod
    def schools_listing(cls):
        return cls.select() \
            .where(cls.student_coupon.is_null(False)) \
            .order_by(cls.name)

    @classmethod
    def active_schools_listing(cls, today=None):
        today = today or date.today()
        return cls.active_listing(today=today) \
            .where(cls.student_coupon.is_null(False)) \
            .order_by(cls.name)

    @classmethod
    def coupons(cls):
        return {partner.coupon for partner
                in cls.select().where(cls.coupon.is_null(False))}

    @classmethod
    def student_coupons(cls):
        return {partner.student_coupon for partner
                in cls.select().where(cls.student_coupon.is_null(False))}

    def __str__(self):
        return self.name


class PartnershipPlan(BaseModel):
    slug = CharField(unique=True)
    name = CharField()
    price = IntegerField()
    limit = IntegerField(null=True)
    includes = ForeignKeyField('self', null=True, backref='list_where_included')
    hierarchy_rank = IntegerField(null=True)

    @property
    def hierarchy(self):
        hierarchy = []
        plan = self
        while True:
            hierarchy.append(plan)
            if plan.includes:
                plan = plan.includes
            else:
                break
        return reversed(hierarchy)

    def benefits(self, all=True):
        for plan in (self.hierarchy if all else [self]):
            yield from plan.list_benefits.order_by(PartnershipBenefit.position)

    @classmethod
    def get_by_slug(cls, slug):
        return cls.select() \
            .where(cls.slug == slug) \
            .get()


class PartnershipBenefit(BaseModel):
    position = IntegerField()
    text = CharField()
    icon = CharField()
    plan = ForeignKeyField(PartnershipPlan, backref='list_benefits')
    slug = CharField(null=True, unique=True)
    quantity = IntegerField(default=1)


class Partnership(BaseModel):
    partner = ForeignKeyField(Partner, backref='list_partnerships')
    plan = ForeignKeyField(PartnershipPlan, null=True, backref='list_partnerships')
    starts_on = DateField(index=True)
    expires_on = DateField(null=True, index=True)


class PartnerStudentSubscription(BaseModel):
    partner = ForeignKeyField(Partner, backref='list_student_subscriptions')
    account_id = CharField()
    name = CharField()
    email = CharField()
    started_on = DateField()
    invoiced_on = DateField(null=True)

    def __str__(self):
        return f'{self.partner.slug}, #{self.account_id}, {self.started_on}, {self.invoiced_on}'